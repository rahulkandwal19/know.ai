import { useState } from "react";
import {cn} from "../../utils/cn"
import { BsMic } from 'react-icons/bs';
import { AiOutlineSearch } from 'react-icons/ai';
export function AskBar({ onAsk, disabled, placeholder = "Ask Know AI", className }) {
  const [value, setValue] = useState("");

  function submit(text) {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onAsk?.(trimmed);
    setValue("");
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        submit(value);
      }}
      className={cn(
        "mx-auto w-full max-w-2xl rounded-xl border border-border  border-gray-300 bg-card px-4 py-3 shadow-sm",
        className
      )}
      aria-label="Ask AI"
      role="search"
    >
      <div className="flex items-center gap-3">
        <AiOutlineSearch className="size-4 text-muted-foreground" aria-hidden="true" />
        <label htmlFor="ask-input" className="sr-only">
          Ask AI
        </label>
        <input
          id="ask-input"
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder}
          className="flex-1 text-base outline-none placeholder:text-muted-foreground"
          disabled={disabled}
          aria-disabled={disabled}
        />
        {/*
        <button
          type="button"
          onClick={() => submit(value)}
          className="inline-flex size-8 items-center justify-center rounded-md bg-muted/60 text-foreground hover:bg-muted"
          aria-label="Send with microphone"
          title="Send"
          disabled={disabled}
        >
          <BsMic className="size-4 opacity-80" aria-hidden="true" />
        </button>
        */}
      </div>
    </form>
  );
}
