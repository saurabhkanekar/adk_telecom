/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef, useState } from "react";
import { VStack, Input, Button, Box, Text, Flex } from "@chakra-ui/react";
import ReactMarkdown from "react-markdown";

const apiBaseUrl = import.meta.env.VITE_BASE_URL;

type Message = {
  from: "user" | "bot" | "system";
  text: string;
  type?: "agent_response" | "processing_agent" | "session_info" | "error"; // Optional type property
  agent_name?: string;
};

const Chatbot = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const messagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesRef.current?.scrollTo({
      top: messagesRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const connectWebSocket = () => {
    const customerId = sessionStorage.getItem("customerId");
    if (!customerId) {
      setMessages([
        { from: "system", text: " No Customer ID found in session." },
      ]);
      return;
    }

    const socket = new WebSocket(`ws://${apiBaseUrl}/chat/${customerId}`);
    ws.current = socket;

    socket.onopen = () => {
      reconnectAttempts.current = 0;
      //   setMessages((prev) => [
      //     ...prev,
      //     { from: "system", text: "WebSocket connected." },
      //   ]);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("WebSocket message received:", data);

      if (data.type === "agent_response") {
        setIsTyping(false);
        setMessages((prev) => [
          // Remove all "processing_agent" messages
          ...prev.filter((msg) => msg.type !== "processing_agent"),
          { from: "bot", text: data.message },
        ]);
      } else if (data.type === "processing_agent") {
        setIsTyping(true);

        const agentName = data.agent_name?.trim();
        const text = agentName
          ? `transferring to ${agentName}`
          : "transferring to agent";

        setMessages((prev) => [
          ...prev,
          {
            from: "bot",
            text,
            type: "processing_agent",
            agent_name: agentName,
          },
        ]);
      } else if (data.type === "session_info") {
        sessionStorage.setItem("customerId", data.customer_id);
      } else if (data.type === "error") {
        setMessages((prev) => [
          ...prev,
          { from: "system", text: `${data.message}` },
        ]);
      }
    };

    socket.onclose = () => {
      //   setMessages((prev) => [
      //     ...prev,
      //     { from: "system", text: "Disconnected. Trying to reconnect..." },
      //   ]);
      setIsTyping(false);
      retryConnection();
    };

    socket.onerror = () => {
      setMessages((prev) => [
        ...prev,
        { from: "system", text: "WebSocket error." },
      ]);
    };
  };

  const retryConnection = () => {
    reconnectAttempts.current += 1;
    const timeout = Math.min(10000, 1000 * reconnectAttempts.current);
    setTimeout(() => {
      connectWebSocket();
    }, timeout);
  };

  useEffect(() => {
    connectWebSocket();
  }, []);

  const sendMessage = () => {
    const trimmed = input.trim();
    if (!trimmed || !ws.current || ws.current.readyState !== WebSocket.OPEN)
      return;

    setMessages((prev) => [...prev, { from: "user", text: trimmed }]);
    setIsTyping(true);

    ws.current.send(JSON.stringify({ type: "user_message", message: trimmed }));
    setInput("");
  };

  return (
    <VStack align="center" width="100%" className="!pt-10">
      <Box
        ref={messagesRef}
        width="100%"
        height="26rem"
        p="16px"
        overflowY="auto"
        // borderRadius="16px"
        boxShadow="lg"
        bg="rgba(255, 255, 255, 0.3)"
        border="1px solid rgba(255, 255, 255, 0.4)"
        style={{
          backdropFilter: "blur(12px)",
        }}
        className="!max-w-[86%] !rounded-4xl "
      >
        {messages.length === 0 ? (
          <Text color="gray.600">Start a conversation</Text>
        ) : (
          messages.map((msg, idx) => (
            <Flex
              key={idx}
              justify={
                msg.from === "user"
                  ? "flex-end"
                  : msg.from === "bot"
                  ? "flex-start"
                  : "center"
              }
              mb="12px"
            >
              <Box
                px="12px"
                py="8px"
                borderRadius="12px"
                maxW="70%"
                fontStyle={msg.from === "system" ? "italic" : "normal"}
                bg={
                  msg.from === "user"
                    ? "linear-gradient(to right, #b272f1, #b273ef)"
                    : msg.from === "bot" && msg.type !== "processing_agent"
                    ? "#dfdfe4"
                    : "transparent"
                }
                color={msg.from === "user" ? "white" : "gray.900"} // White text for user messages
              >
                {msg.from === "bot" || msg.from === "system" ? (
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                ) : (
                  <Text>{msg.text}</Text>
                )}
              </Box>
            </Flex>
          ))
        )}

        {isTyping && (
          <Flex justify="flex-start" mt="8px">
            <Box
              px="16px"
              py="10px"
              bg="#dfdfe4"
              borderRadius="12px"
              display="inline-flex"
              alignItems="center"
              gap="6px"
            >
              {messages[messages.length - 1]?.type === "processing_agent" ? (
                <Text color="gray.700" fontStyle="italic">
                  {messages[messages.length - 1]?.text}
                </Text>
              ) : (
                <>
                  <Box className="typing-dot" />
                  <Box className="typing-dot" />
                  <Box className="typing-dot" />
                </>
              )}
            </Box>
          </Flex>
        )}
      </Box>

      <style>
        {`
    .typing-dot {
      width: 8px;
      height: 8px;
      background-color: #555;
      border-radius: 50%;
      animation: typing-bounce 1.4s infinite;
    }

    .typing-dot:nth-of-type(2) {
      animation-delay: 0.2s;
    }

    .typing-dot:nth-of-type(3) {
      animation-delay: 0.4s;
    }

    @keyframes typing-bounce {
      0%, 80%, 100% {
        transform: translateY(0);
      }
      40% {
        transform: translateY(-8px);
      }
    }
  `}
      </style>

      <Flex width="100%" mt="12px" gap="8px" className="!max-w-[86%] ">
        <Input
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          bg="whiteAlpha.800"
          _focus={{ bg: "whiteAlpha.900" }}
          className="!rounded-full"
        />
        <Button
          onClick={sendMessage}
          bgGradient="linear-gradient(to right, #a351f5, #b273ef)" // Purple gradient
          color="white"
          fontWeight="bold"
          px="24px"
          _hover={{ opacity: 0.9 }}
          className="!rounded-full"
        >
          Send
        </Button>
      </Flex>

      {/* Blinking animation */}
      <style>
        {`
          @keyframes blink {
            0% { opacity: 0.4; }
            50% { opacity: 1; }
            100% { opacity: 0.4; }
          }
        `}
      </style>
    </VStack>
  );
};

export default Chatbot;
