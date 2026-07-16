import { deflateSync } from "node:zlib";

export interface Rgb {
  blue: number;
  green: number;
  red: number;
}

export interface Raster {
  height: number;
  pixels: Uint8Array;
  width: number;
}

export function createRaster(width: number, height: number, color: Rgb): Raster {
  const raster = { height, pixels: new Uint8Array(width * height * 3), width };
  fillRect(raster, 0, 0, width, height, color);
  return raster;
}

export function fillRect(
  raster: Raster,
  x: number,
  y: number,
  width: number,
  height: number,
  color: Rgb,
): void {
  const firstX = Math.max(0, Math.floor(x));
  const firstY = Math.max(0, Math.floor(y));
  const lastX = Math.min(raster.width, Math.ceil(x + width));
  const lastY = Math.min(raster.height, Math.ceil(y + height));
  for (let row = firstY; row < lastY; row += 1) {
    for (let column = firstX; column < lastX; column += 1) setPixel(raster, column, row, color);
  }
}

export function drawLine(
  raster: Raster,
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  color: Rgb,
  thickness = 1,
): void {
  const steps = Math.max(1, Math.ceil(Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0))));
  for (let step = 0; step <= steps; step += 1) {
    const fraction = step / steps;
    const x = Math.round(x0 + (x1 - x0) * fraction);
    const y = Math.round(y0 + (y1 - y0) * fraction);
    fillRect(
      raster,
      x - Math.floor(thickness / 2),
      y - Math.floor(thickness / 2),
      thickness,
      thickness,
      color,
    );
  }
}

export function setPixel(raster: Raster, x: number, y: number, color: Rgb): void {
  if (x < 0 || y < 0 || x >= raster.width || y >= raster.height) return;
  const index = (y * raster.width + x) * 3;
  raster.pixels[index] = color.red;
  raster.pixels[index + 1] = color.green;
  raster.pixels[index + 2] = color.blue;
}

export function encodePng(raster: Raster): Buffer {
  const scanlineLength = raster.width * 3 + 1;
  const scanlines = Buffer.alloc(scanlineLength * raster.height);
  for (let row = 0; row < raster.height; row += 1) {
    const destination = row * scanlineLength;
    scanlines[destination] = 0;
    scanlines.set(
      raster.pixels.subarray(row * raster.width * 3, (row + 1) * raster.width * 3),
      destination + 1,
    );
  }
  const header = Buffer.alloc(13);
  header.writeUInt32BE(raster.width, 0);
  header.writeUInt32BE(raster.height, 4);
  header[8] = 8;
  header[9] = 2;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    pngChunk("IHDR", header),
    pngChunk("IDAT", deflateSync(scanlines)),
    pngChunk("IEND", Buffer.alloc(0)),
  ]);
}

function pngChunk(type: string, data: Buffer): Buffer {
  const typeBytes = Buffer.from(type, "ascii");
  const output = Buffer.alloc(12 + data.length);
  output.writeUInt32BE(data.length, 0);
  typeBytes.copy(output, 4);
  data.copy(output, 8);
  output.writeUInt32BE(crc32(Buffer.concat([typeBytes, data])), output.length - 4);
  return output;
}

function crc32(bytes: Buffer): number {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}
import { Buffer } from "node:buffer";
