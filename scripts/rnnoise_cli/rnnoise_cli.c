#include <errno.h>
#include <limits.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "rnnoise.h"

#define RNNOISE_CLI_VERSION "0.2"

typedef struct {
  const char *input_path;
  const char *output_path;
  bool overwrite;
  bool json;
} CliOptions;

static void print_usage(FILE *stream) {
  fprintf(stream,
          "Usage:\n"
          "  rnnoise-cli --version\n"
          "  rnnoise-cli denoise --input in.s16le --output out.s16le "
          "[--overwrite] [--json]\n");
}

static void print_json_error(const char *message) {
  fprintf(stderr, "{\"ok\":false,\"error\":\"%s\"}\n", message);
}

static void print_error(const CliOptions *options, const char *message) {
  if (options != NULL && options->json) {
    print_json_error(message);
    return;
  }
  fprintf(stderr, "%s\n", message);
}

static bool parse_options(int argc, char **argv, CliOptions *options) {
  memset(options, 0, sizeof(*options));
  if (argc < 2 || strcmp(argv[1], "denoise") != 0) {
    return false;
  }
  for (int i = 2; i < argc; i++) {
    if (strcmp(argv[i], "--input") == 0 && i + 1 < argc) {
      options->input_path = argv[++i];
    } else if (strcmp(argv[i], "--output") == 0 && i + 1 < argc) {
      options->output_path = argv[++i];
    } else if (strcmp(argv[i], "--overwrite") == 0) {
      options->overwrite = true;
    } else if (strcmp(argv[i], "--json") == 0) {
      options->json = true;
    } else {
      return false;
    }
  }
  return options->input_path != NULL && options->output_path != NULL;
}

static bool output_exists(const char *path) {
  FILE *file = fopen(path, "rb");
  if (file == NULL) {
    return false;
  }
  fclose(file);
  return true;
}

static short clamp_float_to_short(float value) {
  if (value > SHRT_MAX) {
    return SHRT_MAX;
  }
  if (value < SHRT_MIN) {
    return SHRT_MIN;
  }
  return (short)value;
}

static int denoise_file(const CliOptions *options) {
  if (!options->overwrite && output_exists(options->output_path)) {
    print_error(options, "Output already exists. Pass --overwrite to replace it.");
    return 3;
  }

  FILE *input = fopen(options->input_path, "rb");
  if (input == NULL) {
    print_error(options, strerror(errno));
    return 4;
  }

  FILE *output = fopen(options->output_path, "wb");
  if (output == NULL) {
    print_error(options, strerror(errno));
    fclose(input);
    return 5;
  }

  DenoiseState *state = rnnoise_create(NULL);
  if (state == NULL) {
    print_error(options, "Could not initialize RNNoise state.");
    fclose(input);
    fclose(output);
    return 6;
  }

  const int frame_size = rnnoise_get_frame_size();
  short *input_frame = calloc((size_t)frame_size, sizeof(short));
  short *output_frame = calloc((size_t)frame_size, sizeof(short));
  float *samples = calloc((size_t)frame_size, sizeof(float));
  if (input_frame == NULL || output_frame == NULL || samples == NULL) {
    print_error(options, "Could not allocate RNNoise frame buffers.");
    free(input_frame);
    free(output_frame);
    free(samples);
    rnnoise_destroy(state);
    fclose(input);
    fclose(output);
    return 7;
  }

  long frames_processed = 0;
  while (true) {
    size_t read_count = fread(input_frame, sizeof(short), (size_t)frame_size, input);
    if (read_count == 0) {
      if (ferror(input)) {
        print_error(options, "Could not read input raw PCM.");
        free(input_frame);
        free(output_frame);
        free(samples);
        rnnoise_destroy(state);
        fclose(input);
        fclose(output);
        return 8;
      }
      break;
    }
    for (size_t i = read_count; i < (size_t)frame_size; i++) {
      input_frame[i] = 0;
    }
    for (int i = 0; i < frame_size; i++) {
      samples[i] = (float)input_frame[i];
    }
    rnnoise_process_frame(state, samples, samples);
    for (int i = 0; i < frame_size; i++) {
      output_frame[i] = clamp_float_to_short(samples[i]);
    }
    if (fwrite(output_frame, sizeof(short), read_count, output) != read_count) {
      print_error(options, "Could not write output raw PCM.");
      free(input_frame);
      free(output_frame);
      free(samples);
      rnnoise_destroy(state);
      fclose(input);
      fclose(output);
      return 9;
    }
    frames_processed++;
    if (read_count < (size_t)frame_size) {
      break;
    }
  }

  free(input_frame);
  free(output_frame);
  free(samples);
  rnnoise_destroy(state);
  fclose(input);
  fclose(output);

  if (options->json) {
    printf("{\"ok\":true,\"frames_processed\":%ld,\"frame_size\":%d}\n",
           frames_processed,
           frame_size);
  }
  return 0;
}

int main(int argc, char **argv) {
  if (argc == 2 && strcmp(argv[1], "--version") == 0) {
    printf("rnnoise-cli %s\n", RNNOISE_CLI_VERSION);
    return 0;
  }

  CliOptions options;
  if (!parse_options(argc, argv, &options)) {
    print_usage(stderr);
    return 2;
  }

  return denoise_file(&options);
}
