export function generateField(size = 50, width = 1000, height = 600): string[] {
  const rowHeight = size * (Math.sqrt(3) / 2);
  const rows = Math.ceil(height / rowHeight) + 2;
  const cols = Math.ceil(width / size) + 3;
  const triangles: string[] = [];

  for (let r = -1; r < rows; r++) {
    const y0 = r * rowHeight;
    const y1 = (r + 1) * rowHeight;
    const offset = r % 2 === 0 ? 0 : size / 2;
    for (let c = -2; c < cols; c++) {
      const x0 = c * size + offset;
      triangles.push(`${x0},${y1} ${x0 + size},${y1} ${x0 + size / 2},${y0}`);
      triangles.push(`${x0 + size / 2},${y0} ${x0 + size * 1.5},${y0} ${x0 + size},${y1}`);
    }
  }
  return triangles;
}
