import { Sequence, AbsoluteFill } from "remotion";
import { Scene1 } from "./scenes/Scene1";
import { Scene2 } from "./scenes/Scene2";
import { Scene3 } from "./scenes/Scene3";
import { Scene4 } from "./scenes/Scene4";
import "./index.css";

export const MainSequence: React.FC = () => {
  return (
    <AbsoluteFill className="bg-slate-950 text-white font-sans">
      <Sequence from={0} durationInFrames={150}>
        <Scene1 />
      </Sequence>
      <Sequence from={150} durationInFrames={300}>
        <Scene2 />
      </Sequence>
      <Sequence from={450} durationInFrames={300}>
        <Scene3 />
      </Sequence>
      <Sequence from={750} durationInFrames={300}>
        <Scene4 />
      </Sequence>
    </AbsoluteFill>
  );
};
