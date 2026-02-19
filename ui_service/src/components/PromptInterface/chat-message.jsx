import { cn } from "../../utils/cn";
import Lottie from "lottie-react";
import knowAIWorking from "../../assets/knowAI/knowAIWorkingPromptIcon.json";
import knowAIDone from "../../assets/knowAI/knowAIDonePromptIcon.png";
import knowAIInterrupted from "../../assets/knowAI/knowAIIntruptedPromptIcon.png";
import MarkdownRenderer from "../../utils/markdownRender"
export default function ChatMessage({ message, role, content }) {
  const derivedRole = role ?? message?.role ?? "assistant";
  const isUser = derivedRole === "user";

  let text = content;
  if (text == null && message) {
    const mc = message.content;
    if (typeof mc === "string") {
      text = mc;
    } else if (Array.isArray(mc)) {
      const firstText = mc.find((p) => typeof p === "string" || p?.type === "text");
      text = typeof firstText === "string" ? firstText : firstText?.text;
    } else if (typeof message.text === "string") {
      text = message.text;
    }
  }

  return (
    <div className={cn("w-full flex mb-8", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <>
          {message?.messageStatus === "done" ? (
            <img src={knowAIDone} className="w-[45px] h-[45px] object-contain" alt="Done" />
          ) : message?.messageStatus === "interrupted" ? (
            <img src={knowAIInterrupted} className="w-[45px] h-[45px] object-contain" alt="Interrupted" />
          ) : (
            <Lottie
              animationData={knowAIWorking}
              loop
              play={true}
              style={{
                width: 60,
                height: 60,
                objectFit: "cover",
                overflow: "hidden",
                transform: "scale(1.5)",
                transformOrigin: "center",
                clipPath: "inset(10% 10% 10% 10%)",
              }}
            />
          )}
        </>
      )}

      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-gray-200 text-gray-800 ml-auto rounded-bl-2xl rounded-tl-2xl rounded-br-2xl rounded-tr"
            : "bg-muted text-foreground"
        )}
        aria-label={isUser ? "User message" : "Assistant message"}
        style={{ whiteSpace: "pre-line" }}
      >
      <MarkdownRenderer content={text ?? ""} />
      </div>
    </div>
  );
}

export { ChatMessage };
