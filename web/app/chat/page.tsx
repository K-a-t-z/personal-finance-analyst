"use client";

import { useState } from "react";
import { queryFinance } from "@/src/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  data?: any; // For assistant messages, store the full response
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [month, setMonth] = useState("");
  const [limitEvidence, setLimitEvidence] = useState<number>(20);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const payload: {
        question: string;
        month?: string;
        limit_evidence?: number;
      } = {
        question: input,
      };

      if (month.trim()) {
        payload.month = month.trim();
      }
      if (limitEvidence > 0) {
        payload.limit_evidence = limitEvidence;
      }

      const response = await queryFinance(payload);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.final_answer || response.clarifying_question || "No response",
        data: response,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : "Failed to get response"}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-zinc-50 dark:bg-black">
      {/* Header */}
      <div className="bg-white dark:bg-zinc-900 border-b border-gray-200 dark:border-gray-800 px-4 py-4">
        <h1 className="text-2xl font-bold text-black dark:text-zinc-50">Chat</h1>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 dark:text-gray-400 py-12">
              <p>Start a conversation by asking a question about your finances.</p>
              <p className="text-sm mt-2">Try: "How much did I spend in 2025-06?"</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  message.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-white dark:bg-zinc-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700"
                }`}
              >
                {message.role === "user" ? (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <AssistantMessage message={message} />
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white dark:bg-zinc-800 rounded-lg px-4 py-3 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Thinking...</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white dark:bg-zinc-900 border-t border-gray-200 dark:border-gray-800 px-4 py-4">
        <div className="max-w-4xl mx-auto space-y-3">
          {/* Optional Inputs */}
          <div className="flex gap-4 text-sm">
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Month (optional, YYYY-MM)
              </label>
              <input
                type="text"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
                placeholder="2025-06"
                pattern="\d{4}-\d{2}"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                  bg-white dark:bg-zinc-800 text-gray-900 dark:text-gray-100
                  focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="w-32">
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Evidence Limit
              </label>
              <input
                type="number"
                value={limitEvidence}
                onChange={(e) => setLimitEvidence(parseInt(e.target.value) || 20)}
                min="1"
                max="100"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                  bg-white dark:bg-zinc-800 text-gray-900 dark:text-gray-100
                  focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Message Input */}
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your finances..."
              rows={2}
              className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                bg-white dark:bg-zinc-800 text-gray-900 dark:text-gray-100
                focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg
                hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function AssistantMessage({ message }: { message: Message }) {
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [traceOpen, setTraceOpen] = useState(false);
  const data = message.data;

  if (!data) {
    return <p className="whitespace-pre-wrap">{message.content}</p>;
  }

  return (
    <div className="space-y-3">
      {/* Main Answer */}
      {data.final_answer && (
        <p className="whitespace-pre-wrap font-medium">{data.final_answer}</p>
      )}
      {data.clarifying_question && (
        <p className="whitespace-pre-wrap text-yellow-600 dark:text-yellow-400 italic">
          {data.clarifying_question}
        </p>
      )}

      {/* Numbers */}
      {data.numbers && Object.keys(data.numbers).length > 0 && (
        <div className="bg-gray-50 dark:bg-zinc-900 rounded p-3 border border-gray-200 dark:border-gray-700">
          <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">Numbers</h4>
          <div className="space-y-1 text-sm">
            {Object.entries(data.numbers).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400 capitalize">
                  {key.replace(/_/g, " ")}:
                </span>
                <span className="text-gray-900 dark:text-gray-100 font-medium">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence Section */}
      <div>
        <button
          onClick={() => setEvidenceOpen(!evidenceOpen)}
          className="flex items-center gap-2 text-sm font-medium text-blue-600 dark:text-blue-400
            hover:text-blue-700 dark:hover:text-blue-300"
        >
          <span>{evidenceOpen ? "▼" : "▶"}</span>
          <span>Evidence ({data.evidence?.length || 0} rows)</span>
        </button>
        {evidenceOpen && (
          <div className="mt-2 overflow-x-auto">
            {data.evidence && data.evidence.length > 0 ? (
              <table className="w-full text-xs border-collapse border border-gray-300 dark:border-gray-600">
                <thead>
                  <tr className="bg-gray-100 dark:bg-zinc-700">
                    <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-left">
                      Date
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-left">
                      Where
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-left">
                      What
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-left">
                      Amount
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-left">
                      Category
                    </th>
                    <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-left">
                      Source
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.evidence.map((row: any, idx: number) => (
                    <tr key={idx} className="bg-white dark:bg-zinc-800">
                      <td className="border border-gray-300 dark:border-gray-600 px-2 py-1">
                        {row.date || "-"}
                      </td>
                      <td className="border border-gray-300 dark:border-gray-600 px-2 py-1">
                        {row.where || "-"}
                      </td>
                      <td className="border border-gray-300 dark:border-gray-600 px-2 py-1">
                        {row.what || "-"}
                      </td>
                      <td className="border border-gray-300 dark:border-gray-600 px-2 py-1">
                        {row.amount ? `$${parseFloat(row.amount).toFixed(2)}` : "-"}
                      </td>
                      <td className="border border-gray-300 dark:border-gray-600 px-2 py-1">
                        {row.category || "-"}
                      </td>
                      <td className="border border-gray-300 dark:border-gray-600 px-2 py-1">
                        {row.source || "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 italic py-2">
                No evidence rows
              </p>
            )}
          </div>
        )}
      </div>

      {/* Trace Section */}
      {data.trace && (
        <div>
          <button
            onClick={() => setTraceOpen(!traceOpen)}
            className="flex items-center gap-2 text-sm font-medium text-blue-600 dark:text-blue-400
              hover:text-blue-700 dark:hover:text-blue-300"
          >
            <span>{traceOpen ? "▼" : "▶"}</span>
            <span>Trace</span>
          </button>
          {traceOpen && (
            <div className="mt-2 bg-gray-50 dark:bg-zinc-900 rounded p-3 border border-gray-200 dark:border-gray-700">
              <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-auto">
                {JSON.stringify(data.trace, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
