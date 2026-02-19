
export async function sendToKnowAI(text) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Request failed");
  }
  const data = await res.json();
  
  return {
    id: data.id ?? crypto.randomUUID(),
    role: data.role ?? "assistant",
    content: data.content ?? data.text ?? "",
    text: data.text ?? data.content ?? "",
  };
}
