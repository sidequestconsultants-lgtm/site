"use client";

import { useLayoutEffect, useRef, useState } from "react";
import type { AnimationEvent } from "react";
import TessellationField from "@/components/brand/TessellationField";

const STORAGE_KEY = "sq-boot-played";

type BootState = "checking" | "playing" | "hidden";

export default function BootScreen() {
  const [state, setState] = useState<BootState>("checking");
  const decided = useRef(false);

  useLayoutEffect(() => {
    if (decided.current) return;
    decided.current = true;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const alreadyPlayed = sessionStorage.getItem(STORAGE_KEY) === "1";

    if (reduceMotion || alreadyPlayed) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- syncing a client-only capability check (sessionStorage/matchMedia) into state; cannot be derived during render or SSR
      setState("hidden");
      return;
    }

    sessionStorage.setItem(STORAGE_KEY, "1");
    setState("playing");
  }, []);

  if (state !== "playing") return null;

  const handleAnimationEnd = (e: AnimationEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && e.animationName === "boot-dissolve") {
      setState("hidden");
    }
  };

  return (
    <div className="boot-overlay" aria-hidden="true" onAnimationEnd={handleAnimationEnd}>
      <TessellationField className="boot-field" size={50} />

      <div className="boot-mark">
        <svg viewBox="0 0 100 100" className="h-full w-full">
          <defs>
            <linearGradient id="boot-grad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#9DD3FF" />
              <stop offset="1" stopColor="#7B6CF0" />
            </linearGradient>
          </defs>
          <g className="boot-brackets" stroke="#EAEDF8" strokeWidth={4} fill="none" strokeLinecap="square">
            <path d="M6 22 V6 H22" />
            <path d="M78 6 H94 V22" />
            <path d="M94 78 V94 H78" />
            <path d="M22 94 H6 V78" />
          </g>
          <path
            className="boot-chevron"
            d="M42 36 L62 50 L42 64"
            fill="none"
            stroke="url(#boot-grad)"
            strokeWidth={8}
            strokeLinecap="square"
            strokeLinejoin="miter"
          />
        </svg>
        <span className="boot-dot" />
      </div>

      <div className="boot-status">
        <span className="boot-type">{"// initialising sidequest"}</span>
        <span className="boot-rule">
          <span className="boot-rule-fill" />
        </span>
      </div>
    </div>
  );
}
