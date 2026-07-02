import "./index.css";
import { Composition } from "remotion";
import { MainSequence } from "./MainSequence";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="PromptEnhancerDemo"
        component={MainSequence}
        durationInFrames={1050}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
