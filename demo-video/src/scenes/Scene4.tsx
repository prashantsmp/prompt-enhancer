import { AbsoluteFill, useCurrentFrame, interpolate, spring, Img, staticFile } from "remotion";
import React from "react";

export const Scene4: React.FC = () => {
  const frame = useCurrentFrame();
  
  // Click at frame 30
  const cursorX = spring({ frame: frame, fps: 30, from: 800, to: 0, durationInFrames: 30 });
  const cursorY = spring({ frame: frame, fps: 30, from: 800, to: 0, durationInFrames: 30 });
  const clickScale = spring({ frame: frame - 30, fps: 30, from: 1, to: 0.9, durationInFrames: 5, config: { damping: 10 } });
  
  const isApproved = frame >= 30;

  // Reveal image at frame 60
  const showReveal = frame >= 60;
  const revealProgress = spring({ frame: frame - 60, fps: 30, from: 0, to: 1, durationInFrames: 60 });
  const imageScale = interpolate(revealProgress, [0, 1], [1.5, 1]);
  const dashboardOpacity = interpolate(revealProgress, [0, 0.5], [1, 0]);

  return (
    <AbsoluteFill className="justify-center items-center bg-slate-950 p-12">
      {/* Background Dashboard */}
      <div className="w-full h-full bg-slate-900 border border-slate-700/50 rounded-2xl flex flex-col overflow-hidden shadow-2xl relative" style={{ opacity: dashboardOpacity }}>
        <div className="h-20 bg-slate-800/80 border-b border-slate-700/50 flex items-center px-8 justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-indigo-500 rounded-lg flex items-center justify-center font-bold text-xl">PE</div>
            <span className="text-2xl font-semibold tracking-wide text-white">PromptEnhancer</span>
          </div>
          
          <div className="flex gap-4 relative">
            <button 
              className="px-6 py-3 rounded-lg bg-emerald-500 text-white font-bold text-lg shadow-lg shadow-emerald-500/30 transform transition-transform"
              style={{ transform: `scale(${frame >= 30 && frame < 35 ? clickScale : 1})` }}
            >
              {isApproved ? "APPROVED" : "APPROVE VIBE DIFF"}
            </button>
            
            {/* Fake Cursor */}
            {!isApproved && (
              <div 
                className="absolute z-50 w-8 h-8 pointer-events-none" 
                style={{ 
                  transform: `translate(${cursorX}px, ${cursorY}px)`,
                  right: '20px',
                  bottom: '-20px'
                }}
              >
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 24L8 8L24 12L17 15L12 24Z" fill="white" stroke="black" strokeWidth="2"/>
                </svg>
              </div>
            )}
          </div>
        </div>

        {/* Loading overlay when approved */}
        {isApproved && !showReveal && (
          <div className="absolute inset-0 bg-slate-950/80 flex flex-col items-center justify-center z-40 backdrop-blur-sm">
            <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <h2 className="text-white text-2xl mt-8 font-light tracking-widest uppercase">Generating Assets...</h2>
          </div>
        )}
      </div>

      {/* The Final Reveal */}
      {showReveal && (
        <AbsoluteFill className="justify-center items-center bg-black z-50 overflow-hidden" style={{ opacity: revealProgress }}>
          <Img 
            src={staticFile("cat_on_skateboard.png")} 
            className="w-full h-full object-cover" 
            style={{ transform: `scale(${imageScale})` }} 
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex items-end justify-center pb-20">
            <h1 className="text-white text-6xl font-bold tracking-tight shadow-black drop-shadow-2xl" style={{ opacity: interpolate(revealProgress, [0.5, 1], [0, 1]) }}>
              PromptEnhancer
            </h1>
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
