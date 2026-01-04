import React, { useState, useRef, useEffect } from "react";
import { sendChatMessage, getChatModels, checkOllamaHealth } from "../../services/api";
import "./Chatbot.css";

function Chatbot() {
    const [messages, setMessages] = useState([
        {
            role: "assistant",
            content: "Hello! I'm your building assistant. How can I help you optimize your smart building today?",
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [models, setModels] = useState([]);
    const [selectedModel, setSelectedModel] = useState("llama3.2:latest");
    const [isOllamaHealthy, setIsOllamaHealthy] = useState(true);
    const [isMinimized, setIsMinimized] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Auto-scroll to bottom
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Check Ollama health and load models on mount
    useEffect(() => {
        async function initializeChat() {
            try {
                const health = await checkOllamaHealth();
                setIsOllamaHealthy(health.status === "healthy");

                if (health.status === "healthy") {
                    const modelsData = await getChatModels();
                    setModels(modelsData.models || []);
                    if (modelsData.models?.length > 0) {
                        setSelectedModel(modelsData.models[0]);
                    }
                }
            } catch (error) {
                console.error("Failed to initialize chat:", error);
                setIsOllamaHealthy(false);
            }
        }
        initializeChat();
    }, []);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !isOllamaHealthy) return;

        const userMessage = {
            role: "user",
            content: input,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const response = await sendChatMessage({
                messages: [...messages, userMessage],
                model: selectedModel,
            });

            const assistantMessage = {
                role: "assistant",
                content: response.response,
                timestamp: new Date(response.timestamp),
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            const errorMessage = {
                role: "assistant",
                content: "Sorry, I encountered an error. Please make sure Ollama is running and try again.",
                timestamp: new Date(),
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(e);
        }
    };

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    if (isMinimized) {
        return (
            <div className="chatbot-minimized" onClick={() => setIsMinimized(false)}>
                <div className="chatbot-minimized-content">
                    <span className="chatbot-icon">💬</span>
                    <span className="chatbot-status">
                        {isOllamaHealthy ? "Online" : "Offline"}
                    </span>
                </div>
            </div>
        );
    }

    return (
        <div className="chatbot-container">
            <div className="chatbot-header">
                <div className="chatbot-title">
                    <h3>Building Assistant</h3>
                    <span className={`status-indicator ${isOllamaHealthy ? "online" : "offline"}`}>
                        {isOllamaHealthy ? "● Online" : "● Offline"}
                    </span>
                </div>
                <div className="chatbot-controls">
                    {models.length > 0 && (
                        <select
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                            className="model-selector"
                            disabled={isLoading}
                        >
                            {models.map((model) => (
                                <option key={model} value={model}>
                                    {model}
                                </option>
                            ))}
                        </select>
                    )}
                    <button
                        className="minimize-button"
                        onClick={() => setIsMinimized(true)}
                    >
                        −
                    </button>
                </div>
            </div>

            <div className="chatbot-messages">
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={`message ${message.role}`}
                    >
                        <div className="message-content">
                            <p>{message.content}</p>
                            <span className="message-time">
                                {formatTimestamp(message.timestamp)}
                            </span>
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="message assistant">
                        <div className="message-content loading">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {!isOllamaHealthy && (
                <div className="chatbot-error">
                    <p>
                        ⚠️ Ollama is not running. Please start Ollama to use the chatbot.
                    </p>
                    <p>
                        Run: <code>ollama serve</code> in your terminal
                    </p>
                </div>
            )}

            <form onSubmit={handleSendMessage} className="chatbot-input">
                <div className="input-container">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder={
                            isOllamaHealthy
                                ? "Ask about energy optimization, anomalies, or building management..."
                                : "Chatbot unavailable - Ollama not running"
                        }
                        disabled={isLoading || !isOllamaHealthy}
                        className="message-input"
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !isOllamaHealthy || !input.trim()}
                        className="send-button"
                    >
                        {isLoading ? "..." : "Send"}
                    </button>
                </div>
            </form>
        </div>
    );
}

export default Chatbot;
