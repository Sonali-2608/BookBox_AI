import ChatInterface from "../components/ChatInterface.jsx";

export default function Chat() {
  return (
    <div className="mx-auto max-w-3xl">
      <span className="eyebrow">Ask Lexora</span>
      <h1 className="mt-2 font-display text-3xl font-medium text-parchment">
        Your reading assistant.
      </h1>
      <p className="mt-2 text-sm text-parchment/60">
        Grounded in books already in the catalog — Lexora won't recommend a title it can't
        actually show you.
      </p>

      <div className="mt-8">
        <ChatInterface />
      </div>
    </div>
  );
}
