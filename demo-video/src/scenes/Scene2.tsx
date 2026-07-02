import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";
import React from "react";

export const Scene2: React.FC = () => {
  const frame = useCurrentFrame();

  const generatedPrompt = 
    `1. Opening: A highly detailed, cinematic rendering of a cute fluffy orange cat riding a skateboard.\n` +
    `2. Spatially Organized Body: The cat is positioned in the center, surfing down a neon-lit cyberpunk city street. Puddles reflect the vivid pink and cyan neon signs.\n` +
    `3. Hierarchical Object Description: The cat wears a glowing LED harness. The skateboard is sleek, matte black with luminescent turquoise wheels.\n` +
    `4. Concluding Style: Shallow depth of field, dramatic moody lighting, highly realistic, 8k resolution, octane render.`;

  // Starts typing at frame 30, fast typing
  const typingFrame = Math.max(0, frame - 30);
  const charsShown = Math.min(generatedPrompt.length, Math.floor(typingFrame * 2));
  const displayedText = generatedPrompt.substring(0, charsShown);

  const opacity = interpolate(frame, [0, 15], [0, 1]);

  return (
    <AbsoluteFill className="justify-center items-center bg-slate-950 px-24 py-16" style={{ opacity }}>
      <div className="w-full max-w-5xl">
        <h2 className="text-gray-400 text-3xl mb-6 font-light tracking-widest uppercase">
          Agentic Rewriter (CoT)
        </h2>
        <div className="w-full h-[600px] bg-slate-900 border border-slate-700 rounded-xl p-8 shadow-2xl shadow-indigo-500/20 flex flex-col font-mono relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-8 bg-slate-800 flex items-center px-4 gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-slate-400 text-xs ml-4">agent.session.run</span>
          </div>
          
          <div className="mt-8 text-xl text-emerald-400 whitespace-pre-wrap leading-relaxed">
            {displayedText}
            {frame % 20 < 10 && charsShown < generatedPrompt.length ? <span className="opacity-100 bg-emerald-400 text-emerald-400">_</span> : null}
          </div>
          
          {charsShown >= generatedPrompt.length && (
            <div className="mt-8 text-indigo-400 animate-pulse text-xl">
              [Evaluator Score: 5/5] -&gt; Proceeding to Vibe Diff...
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
