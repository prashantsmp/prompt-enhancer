import { AbsoluteFill, useCurrentFrame, spring } from "remotion";
import React from "react";

export const Scene1: React.FC = () => {
  const frame = useCurrentFrame();
  const text = "A cute cat on a skateboard";
  
  // Start typing at frame 30
  const typingFrame = Math.max(0, frame - 30);
  const charsShown = Math.min(text.length, Math.floor(typingFrame / 2));
  const displayedText = text.substring(0, charsShown);

  return (
    <AbsoluteFill className="justify-center items-center bg-slate-950">
      <div className="flex flex-col items-center">
        <h2 className="text-gray-400 text-3xl mb-8 font-light tracking-widest uppercase">
          Standard Prompts
        </h2>
        <div className="w-[800px] h-24 bg-slate-900 border border-slate-700 rounded-xl flex items-center px-8 shadow-2xl shadow-indigo-500/10">
          <span className="text-4xl font-mono text-emerald-400">
            {displayedText}
            {frame % 30 < 15 ? <span className="opacity-100">|</span> : <span className="opacity-0">|</span>}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
