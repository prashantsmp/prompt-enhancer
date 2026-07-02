import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";
import React from "react";

export const Scene3: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1]);

  return (
    <AbsoluteFill className="justify-center items-center bg-slate-950 p-12" style={{ opacity }}>
      <div className="w-full h-full bg-slate-900 border border-slate-700/50 rounded-2xl flex flex-col overflow-hidden shadow-2xl relative">
        {/* Header */}
        <div className="h-20 bg-slate-800/80 border-b border-slate-700/50 flex items-center px-8 justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-indigo-500 rounded-lg flex items-center justify-center font-bold text-xl">PE</div>
            <span className="text-2xl font-semibold tracking-wide text-white">PromptEnhancer</span>
          </div>
          <div className="px-4 py-2 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 text-sm font-semibold tracking-widest">
            PENDING APPROVAL
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-12 flex gap-8">
          {/* Original Prompt */}
          <div className="flex-1 bg-slate-800/50 border border-slate-700 rounded-xl p-8 flex flex-col">
            <h3 className="text-slate-400 text-lg uppercase tracking-wider mb-4">Original Prompt</h3>
            <div className="text-slate-300 text-2xl font-light">
              "A cute cat on a skateboard"
            </div>
          </div>

          {/* New Prompt */}
          <div className="flex-1 bg-indigo-900/20 border border-indigo-500/30 rounded-xl p-8 flex flex-col shadow-[0_0_50px_rgba(99,102,241,0.1)]">
            <h3 className="text-indigo-400 text-lg uppercase tracking-wider mb-4">Enhanced Prompt</h3>
            <div className="text-slate-300 text-xl font-light leading-relaxed">
              <span className="text-indigo-300 font-medium">1. Opening:</span> A highly detailed, cinematic rendering of a cute fluffy orange cat riding a skateboard.<br/><br/>
              <span className="text-indigo-300 font-medium">2. Spatially Organized Body:</span> The cat is positioned in the center, surfing down a neon-lit cyberpunk city street...<br/><br/>
              <span className="text-indigo-300 font-medium">3. Hierarchical Object Description:</span> The cat wears a glowing LED harness...<br/><br/>
              <span className="text-indigo-300 font-medium">4. Concluding Style:</span> Shallow depth of field, dramatic moody lighting, highly realistic, 8k resolution...
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
