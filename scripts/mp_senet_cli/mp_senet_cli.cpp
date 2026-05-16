#include <torch/script.h>
#include <torch/torch.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr const char* kVersion = "0.1";
constexpr int kExpectedSampleRate = 16000;
constexpr int kNFft = 400;
constexpr int kHopSize = 100;
constexpr int kWinSize = 400;
constexpr float kCompressFactor = 0.3f;

constexpr int kExitUsage = 2;
constexpr int kExitInputError = 3;
constexpr int kExitModelError = 4;
constexpr int kExitRuntimeError = 5;

struct WaveData {
  uint32_t sample_rate = 0;
  uint16_t channels = 0;
  std::vector<float> samples;
};

struct CliOptions {
  std::string subcommand;
  std::string input_path;
  std::string output_path;
  std::string model_path;
  std::string model_dir;
  int threads = 0;
  bool overwrite = false;
  bool json = false;
  bool help = false;
  bool version = false;
};

template <typename T>
T ReadLittleEndian(std::istream& stream) {
  T value{};
  stream.read(reinterpret_cast<char*>(&value), sizeof(T));
  if (!stream) {
    throw std::runtime_error("Unexpected EOF while reading WAV");
  }
  return value;
}

void WriteLittleEndian(std::ostream& stream, uint32_t value) {
  stream.write(reinterpret_cast<const char*>(&value), sizeof(value));
}

void WriteLittleEndian16(std::ostream& stream, uint16_t value) {
  stream.write(reinterpret_cast<const char*>(&value), sizeof(value));
}

float DecodePcm(const std::vector<uint8_t>& bytes, std::size_t offset, uint16_t bits_per_sample) {
  switch (bits_per_sample) {
    case 8:
      return (static_cast<int>(bytes[offset]) - 128) / 128.0f;
    case 16: {
      const auto value = static_cast<int16_t>(bytes[offset] | (bytes[offset + 1] << 8));
      return static_cast<float>(value) / 32768.0f;
    }
    case 24: {
      int32_t value = static_cast<int32_t>(bytes[offset] | (bytes[offset + 1] << 8) |
                                           (bytes[offset + 2] << 16));
      if ((value & 0x00800000) != 0) {
        value |= 0xFF000000;
      }
      return static_cast<float>(value) / 8388608.0f;
    }
    case 32: {
      const auto value = static_cast<int32_t>(bytes[offset] | (bytes[offset + 1] << 8) |
                                              (bytes[offset + 2] << 16) |
                                              (bytes[offset + 3] << 24));
      return static_cast<float>(value) / 2147483648.0f;
    }
    default:
      throw std::runtime_error("Unsupported PCM bit depth");
  }
}

int16_t EncodePcm16(float sample) {
  sample = std::max(-1.0f, std::min(1.0f, sample));
  return static_cast<int16_t>(std::lrint(sample * 32767.0f));
}

std::string EscapeJson(const std::string& input) {
  std::ostringstream out;
  for (char c : input) {
    switch (c) {
      case '\\':
        out << "\\\\";
        break;
      case '"':
        out << "\\\"";
        break;
      case '\n':
        out << "\\n";
        break;
      case '\r':
        out << "\\r";
        break;
      case '\t':
        out << "\\t";
        break;
      default:
        out << c;
        break;
    }
  }
  return out.str();
}

std::string JsonObject(const std::vector<std::pair<std::string, std::string>>& entries) {
  std::ostringstream out;
  out << "{";
  for (std::size_t i = 0; i < entries.size(); ++i) {
    if (i != 0) {
      out << ",";
    }
    out << "\"" << EscapeJson(entries[i].first) << "\":" << entries[i].second;
  }
  out << "}";
  return out.str();
}

std::string RequireValue(int& index, int argc, char** argv, const std::string& flag) {
  if (index + 1 >= argc) {
    throw std::runtime_error("Missing value for " + flag);
  }
  ++index;
  return argv[index];
}

CliOptions ParseCli(int argc, char** argv) {
  CliOptions options;
  if (argc <= 1) {
    options.help = true;
    return options;
  }

  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    if (arg == "--help" || arg == "-h") {
      options.help = true;
      return options;
    }
    if (arg == "--version") {
      options.version = true;
      return options;
    }
    if (options.subcommand.empty()) {
      options.subcommand = arg;
      continue;
    }
    if (arg == "--input") {
      options.input_path = RequireValue(i, argc, argv, arg);
    } else if (arg == "--output") {
      options.output_path = RequireValue(i, argc, argv, arg);
    } else if (arg == "--model") {
      options.model_path = RequireValue(i, argc, argv, arg);
    } else if (arg == "--model-dir") {
      options.model_dir = RequireValue(i, argc, argv, arg);
    } else if (arg == "--threads") {
      options.threads = std::stoi(RequireValue(i, argc, argv, arg));
      if (options.threads < 0) {
        throw std::runtime_error("--threads must be non-negative");
      }
    } else if (arg == "--overwrite") {
      options.overwrite = true;
    } else if (arg == "--json") {
      options.json = true;
    } else {
      throw std::runtime_error("Unknown argument: " + arg);
    }
  }

  if (options.subcommand != "denoise") {
    throw std::runtime_error("Only the 'denoise' subcommand is supported");
  }
  if (options.input_path.empty()) {
    throw std::runtime_error("--input is required");
  }
  if (options.output_path.empty()) {
    throw std::runtime_error("--output is required");
  }
  return options;
}

std::string HelpText() {
  return "mp-senet-cli denoise --input /path/in.wav --output /path/out.wav "
         "[--model /path/mp_senet_vb.torchscript.pt] [--model-dir /path/models] "
         "[--threads N] [--overwrite] [--json]\n";
}

std::string VersionText() {
  return std::string("mp-senet-cli ") + kVersion + "\n";
}

void PrintError(const std::string& message, bool json, int exit_code) {
  if (json) {
    std::cout << JsonObject({
                     {"ok", "false"},
                     {"exit_code", std::to_string(exit_code)},
                     {"error", "\"" + EscapeJson(message) + "\""},
                 })
              << "\n";
  } else {
    std::cerr << "error: " << message << "\n";
  }
}

WaveData ReadWavFile(const std::string& path) {
  std::ifstream stream(path, std::ios::binary);
  if (!stream) {
    throw std::runtime_error("Unable to open WAV file: " + path);
  }

  char riff[4];
  stream.read(riff, 4);
  const uint32_t riff_size = ReadLittleEndian<uint32_t>(stream);
  (void)riff_size;
  char wave[4];
  stream.read(wave, 4);
  if (std::strncmp(riff, "RIFF", 4) != 0 || std::strncmp(wave, "WAVE", 4) != 0) {
    throw std::runtime_error("Input is not a RIFF/WAVE file");
  }

  uint16_t audio_format = 0;
  uint16_t channels = 0;
  uint32_t sample_rate = 0;
  uint16_t bits_per_sample = 0;
  std::vector<uint8_t> pcm;

  while (stream) {
    char chunk_id[4];
    stream.read(chunk_id, 4);
    if (!stream) {
      break;
    }
    const uint32_t chunk_size = ReadLittleEndian<uint32_t>(stream);
    const std::streampos chunk_start = stream.tellg();

    if (std::strncmp(chunk_id, "fmt ", 4) == 0) {
      audio_format = ReadLittleEndian<uint16_t>(stream);
      channels = ReadLittleEndian<uint16_t>(stream);
      sample_rate = ReadLittleEndian<uint32_t>(stream);
      const uint32_t byte_rate = ReadLittleEndian<uint32_t>(stream);
      (void)byte_rate;
      const uint16_t block_align = ReadLittleEndian<uint16_t>(stream);
      (void)block_align;
      bits_per_sample = ReadLittleEndian<uint16_t>(stream);
    } else if (std::strncmp(chunk_id, "data", 4) == 0) {
      pcm.resize(chunk_size);
      stream.read(reinterpret_cast<char*>(pcm.data()), static_cast<std::streamsize>(pcm.size()));
    }

    stream.seekg(chunk_start + static_cast<std::streamoff>(chunk_size + (chunk_size % 2)));
  }

  if (audio_format != 1) {
    throw std::runtime_error("Only PCM WAV input is supported");
  }
  if (channels == 0 || sample_rate == 0 || bits_per_sample == 0 || pcm.empty()) {
    throw std::runtime_error("WAV file is missing required fmt/data chunks");
  }

  const std::size_t bytes_per_sample = bits_per_sample / 8;
  if (bytes_per_sample == 0 || (pcm.size() % (bytes_per_sample * channels)) != 0) {
    throw std::runtime_error("WAV file has an invalid PCM layout");
  }

  WaveData wave_data;
  wave_data.sample_rate = sample_rate;
  wave_data.channels = channels;
  wave_data.samples.resize(pcm.size() / bytes_per_sample);

  for (std::size_t i = 0, offset = 0; i < wave_data.samples.size(); ++i, offset += bytes_per_sample) {
    wave_data.samples[i] = DecodePcm(pcm, offset, bits_per_sample);
  }
  return wave_data;
}

std::vector<float> DownmixToMono(const WaveData& wave) {
  if (wave.channels == 0) {
    throw std::runtime_error("Wave data has zero channels");
  }
  if (wave.channels == 1) {
    return wave.samples;
  }

  const std::size_t frames = wave.samples.size() / wave.channels;
  std::vector<float> mono(frames, 0.0f);
  for (std::size_t frame = 0; frame < frames; ++frame) {
    float sum = 0.0f;
    for (uint16_t channel = 0; channel < wave.channels; ++channel) {
      sum += wave.samples[frame * wave.channels + channel];
    }
    mono[frame] = sum / static_cast<float>(wave.channels);
  }
  return mono;
}

void WriteWavFile(const std::string& path, const std::vector<float>& samples, uint32_t sample_rate) {
  std::ofstream stream(path, std::ios::binary);
  if (!stream) {
    throw std::runtime_error("Unable to create WAV file: " + path);
  }

  const uint32_t data_size = static_cast<uint32_t>(samples.size() * sizeof(int16_t));
  const uint32_t riff_size = 36 + data_size;
  const uint16_t channels = 1;
  const uint16_t bits_per_sample = 16;
  const uint16_t block_align = channels * (bits_per_sample / 8);
  const uint32_t byte_rate = sample_rate * block_align;

  stream.write("RIFF", 4);
  WriteLittleEndian(stream, riff_size);
  stream.write("WAVE", 4);
  stream.write("fmt ", 4);
  WriteLittleEndian(stream, 16);
  WriteLittleEndian16(stream, 1);
  WriteLittleEndian16(stream, channels);
  WriteLittleEndian(stream, sample_rate);
  WriteLittleEndian(stream, byte_rate);
  WriteLittleEndian16(stream, block_align);
  WriteLittleEndian16(stream, bits_per_sample);
  stream.write("data", 4);
  WriteLittleEndian(stream, data_size);

  for (float sample : samples) {
    const int16_t encoded = EncodePcm16(sample);
    stream.write(reinterpret_cast<const char*>(&encoded), sizeof(encoded));
  }
}

std::filesystem::path DefaultModelPath(const char* argv0, const CliOptions& options) {
  if (!options.model_path.empty()) {
    return options.model_path;
  }
  if (!options.model_dir.empty()) {
    return std::filesystem::path(options.model_dir) / "mp_senet_vb.torchscript.pt";
  }

  const auto executable_path = std::filesystem::absolute(argv0);
  return executable_path.parent_path().parent_path() / "models" / "mp_senet_vb.torchscript.pt";
}

std::vector<float> TensorToVector(torch::Tensor tensor) {
  tensor = tensor.squeeze().contiguous().to(torch::kCPU);
  std::vector<float> samples(static_cast<std::size_t>(tensor.numel()));
  std::memcpy(samples.data(), tensor.data_ptr<float>(), samples.size() * sizeof(float));
  return samples;
}

std::vector<float> EnhanceWithMpSenet(torch::jit::script::Module& model, const std::vector<float>& mono) {
  if (mono.empty()) {
    throw std::runtime_error("Input WAV has no samples");
  }

  torch::NoGradGuard no_grad;
  auto audio = torch::from_blob(
                   const_cast<float*>(mono.data()),
                   {static_cast<int64_t>(mono.size())},
                   torch::TensorOptions().dtype(torch::kFloat32))
                   .clone();

  const auto energy = audio.pow(2.0).sum().item<float>();
  float norm_factor = 1.0f;
  if (energy > 1e-12f) {
    norm_factor = std::sqrt(static_cast<float>(mono.size()) / energy);
  }
  audio = (audio * norm_factor).unsqueeze(0);

  const auto window = torch::hann_window(kWinSize, torch::TensorOptions().dtype(torch::kFloat32));
  auto stft = audio.stft(
      kNFft,
      kHopSize,
      kWinSize,
      window,
      true,
      "reflect",
      false,
      true,
      true,
      std::nullopt);

  const auto real = torch::real(stft);
  const auto imag = torch::imag(stft);
  auto mag = torch::sqrt(real.pow(2.0) + imag.pow(2.0) + 1e-9);
  const auto pha = torch::atan2(imag + 1e-10, real + 1e-5);
  mag = torch::pow(mag, kCompressFactor);

  auto output = model.forward({mag, pha});
  auto tuple = output.toTuple();
  if (tuple->elements().size() < 2) {
    throw std::runtime_error("MP-SENet model returned an unexpected output tuple");
  }

  auto enhanced_mag = tuple->elements()[0].toTensor();
  auto enhanced_pha = tuple->elements()[1].toTensor();
  enhanced_mag = torch::pow(enhanced_mag, 1.0f / kCompressFactor);
  auto enhanced_complex = torch::complex(
      enhanced_mag * torch::cos(enhanced_pha),
      enhanced_mag * torch::sin(enhanced_pha));

  auto enhanced_audio = enhanced_complex.istft(
      kNFft,
      kHopSize,
      kWinSize,
      window,
      true,
      false,
      std::nullopt,
      static_cast<int64_t>(mono.size()),
      false);
  enhanced_audio = enhanced_audio / norm_factor;
  return TensorToVector(enhanced_audio);
}

int ExitCodeForMessage(const std::string& message) {
  if (message.find("model") != std::string::npos || message.find(".pt") != std::string::npos ||
      message.find("PytorchStreamReader") != std::string::npos) {
    return kExitModelError;
  }
  if (message.find("WAV") != std::string::npos || message.find("Input") != std::string::npos ||
      message.find("Output file exists") != std::string::npos || message.find("sample rate") != std::string::npos) {
    return kExitInputError;
  }
  return kExitRuntimeError;
}

}  // namespace

int main(int argc, char** argv) {
  CliOptions options;
  try {
    options = ParseCli(argc, argv);
  } catch (const std::exception& e) {
    PrintError(e.what(), false, kExitUsage);
    std::cerr << HelpText();
    return kExitUsage;
  }

  if (options.help) {
    std::cout << HelpText();
    return 0;
  }
  if (options.version) {
    std::cout << VersionText();
    return 0;
  }

  try {
    const auto output_path = std::filesystem::path(options.output_path);
    if (std::filesystem::exists(output_path) && !options.overwrite) {
      throw std::runtime_error("Output file exists; pass --overwrite to replace it");
    }
    if (options.threads > 0) {
      at::set_num_threads(options.threads);
      at::set_num_interop_threads(1);
    }

    const auto model_path = DefaultModelPath(argv[0], options);
    if (!std::filesystem::is_regular_file(model_path)) {
      throw std::runtime_error("MP-SENet model file is missing: " + model_path.string());
    }

    const auto started = std::chrono::steady_clock::now();
    auto model = torch::jit::load(model_path.string(), torch::kCPU);
    model.eval();

    const WaveData wave = ReadWavFile(options.input_path);
    if (wave.sample_rate != kExpectedSampleRate) {
      throw std::runtime_error("MP-SENet expects a 16 kHz WAV input");
    }
    const std::vector<float> mono = DownmixToMono(wave);
    const std::vector<float> enhanced = EnhanceWithMpSenet(model, mono);
    WriteWavFile(options.output_path, enhanced, kExpectedSampleRate);
    const auto finished = std::chrono::steady_clock::now();
    const auto processing_seconds =
        std::chrono::duration<double>(finished - started).count();

    if (options.json) {
      std::cout << JsonObject({
                       {"ok", "true"},
                       {"output_path", "\"" + EscapeJson(options.output_path) + "\""},
                       {"model_path", "\"" + EscapeJson(model_path.string()) + "\""},
                       {"output_sample_rate", std::to_string(kExpectedSampleRate)},
                       {"output_samples", std::to_string(enhanced.size())},
                       {"processing_duration_seconds", std::to_string(processing_seconds)},
                   })
                << "\n";
    } else {
      std::cout << "Wrote " << options.output_path << " (" << enhanced.size() << " samples @ "
                << kExpectedSampleRate << " Hz)\n";
    }
    return 0;
  } catch (const std::exception& e) {
    const int exit_code = ExitCodeForMessage(e.what());
    PrintError(e.what(), options.json, exit_code);
    return exit_code;
  }
}
