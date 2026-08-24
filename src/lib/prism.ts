export interface Point {
  x: number;
  y: number;
}

export interface PrismFacet {
  points: string;
  fill: string;
  opacity: number;
  shimmer: boolean;
  delay: number;
}

export interface PrismLine {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  opacity: number;
}

export interface PrismRing {
  points: string;
  opacity: number;
}

export interface PrismData {
  facets: PrismFacet[];
  radialLines: PrismLine[];
  crossLines: PrismLine[];
  rings: PrismRing[];
  outline: string;
}

const lerp = (a: Point, b: Point, t: number): Point => ({
  x: a.x + (b.x - a.x) * t,
  y: a.y + (b.y - a.y) * t,
});

export function generatePrism(): PrismData {
  const apex: Point = { x: 200, y: 44 };
  const bl: Point = { x: 56, y: 340 };
  const br: Point = { x: 344, y: 340 };
  const cen: Point = { x: 200, y: 222 };
  const N = 8;
  const maxDist = 190;

  const P = (r: number, k: number): Point => {
    if (r === 0) return apex;
    const le = lerp(apex, bl, r / N);
    const re = lerp(apex, br, r / N);
    return lerp(le, re, k / r);
  };

  const facets: PrismFacet[] = [];
  const addFacet = (a: Point, b: Point, c: Point, i: number) => {
    const mx = (a.x + b.x + c.x) / 3;
    const my = (a.y + b.y + c.y) / 3;
    const d = Math.hypot(mx - cen.x, my - cen.y);
    const t = Math.max(0, 1 - d / maxDist);
    const g = t * t;
    const color = g > 0.6 ? "#CFE6FF" : g > 0.32 ? "#8FA4F5" : "#4E47AE";
    facets.push({
      points: `${a.x},${a.y} ${b.x},${b.y} ${c.x},${c.y}`,
      fill: color,
      opacity: Number((0.05 + g * 0.62).toFixed(3)),
      shimmer: g > 0.35 && i % 3 === 0,
      delay: (i % 7) * 0.4,
    });
  };

  let idx = 0;
  for (let r = 0; r < N; r++) {
    for (let k = 0; k <= r; k++) {
      addFacet(P(r, k), P(r + 1, k), P(r + 1, k + 1), idx++);
      if (k < r) addFacet(P(r, k), P(r, k + 1), P(r + 1, k + 1), idx++);
    }
  }

  const radialLines: PrismLine[] = [];
  for (let r = 1; r <= N; r++) {
    const a = P(r, 0);
    const b = P(r, r);
    radialLines.push({ x1: a.x, y1: a.y, x2: b.x, y2: b.y, opacity: 0.4 });
  }

  const crossLines: PrismLine[] = [];
  for (let k = 1; k < N; k++) {
    const a = P(k, 0);
    const b = P(N, k);
    crossLines.push({ x1: a.x, y1: a.y, x2: b.x, y2: b.y, opacity: 0.32 });
    const c = P(k, k);
    const d = P(N, N - k);
    crossLines.push({ x1: c.x, y1: c.y, x2: d.x, y2: d.y, opacity: 0.32 });
  }

  const rings: PrismRing[] = [];
  for (let s = 1; s <= 3; s++) {
    const t = s * 0.15;
    const ia = lerp(apex, cen, t);
    const ii = lerp(bl, cen, t);
    const ij = lerp(br, cen, t);
    rings.push({
      points: `${ia.x},${ia.y} ${ii.x},${ii.y} ${ij.x},${ij.y}`,
      opacity: Number((0.3 * (1 - t)).toFixed(2)),
    });
  }

  const outline = `${apex.x},${apex.y} ${bl.x},${bl.y} ${br.x},${br.y}`;

  return { facets, radialLines, crossLines, rings, outline };
}

export interface PrismHaloShard {
  points: string;
}

/** Rotating halo of 3 thin shard-triangles around the prism (the ".prism-halo" group). */
export function generatePrismHalo(): PrismHaloShard[] {
  const shards: PrismHaloShard[] = [];
  const Rr = 205;
  for (let i = 0; i < 3; i++) {
    const ang = i * 2.094;
    const p1x = 200 + Math.cos(ang - 1.571) * Rr;
    const p1y = 200 + Math.sin(ang - 1.571) * Rr;
    const p2x = 200 + Math.cos(ang + 0.6 - 1.571) * Rr;
    const p2y = 200 + Math.sin(ang + 0.6 - 1.571) * Rr;
    const p3x = 200 + Math.cos(ang + 0.3 - 1.571) * (Rr - 16);
    const p3y = 200 + Math.sin(ang + 0.3 - 1.571) * (Rr - 16);
    shards.push({ points: `${p1x},${p1y} ${p2x},${p2y} ${p3x},${p3y}` });
  }
  return shards;
}
