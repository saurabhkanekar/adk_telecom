/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
(window as any).chatWebSocket = null;

import React, { useState, useRef } from "react";
import {
  Box,
  Button,
  Input,
  HStack,
  VStack,
  Text,
  Skeleton,
} from "@chakra-ui/react";

import { useNavigate } from "react-router-dom";
import bgImage from "@/assets/airtel-bg-5.jpg";
const apiBaseUrl = import.meta.env.VITE_BASE_URL;

const customerData = [
  { number: "9765822200", id: 101 },
  { number: "9765822201", id: 102 },
  { number: "9765822202", id: 103 },
];

const Login = () => {
  const navigate = useNavigate();

  const [loginMode, setLoginMode] = useState<"admin" | "customer" | null>(null);

  // Admin login state
  const [adminUsername, setAdminUsername] = useState("");
  const [adminPassword, setAdminPassword] = useState("");

  // Customer login state
  const [phone, setPhone] = useState("");
  const [showOTP, setShowOTP] = useState(false);
  const [otp, setOtp] = useState(["", "", "", ""]);
  const [customerId, setCustomerId] = useState<number | null>(null);
  const [error, setError] = useState<string>("");
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (/^\d{0,10}$/.test(val)) {
      setPhone(val);
    }
  };

  const handleOTPChange = (index: number, value: string) => {
    if (/^\d?$/.test(value)) {
      const newOtp = [...otp];
      newOtp[index] = value;
      setOtp(newOtp);
    }

    if (value && index < otp.length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleSendOTP = () => {
    const customer = customerData.find((data) => data.number === phone);
    if (customer) {
      setCustomerId(customer.id);
      setShowOTP(true);
      setError("");

      setTimeout(() => {
        setOtp(["1", "2", "3", "4"]);
      }, 1000); // 1000ms delay before filling the OTP
    } else {
      setError("Please enter a valid number.");
    }
  };

  const handleLogin = () => {
    const enteredOtp = otp.join("");
    if (enteredOtp === "1234" && customerId !== null) {
      setIsLoading(true);
      try {
        const socket = new WebSocket(`ws://${apiBaseUrl}/chat/${customerId}`);
        (window as any).chatWebSocket = socket;

        socket.onopen = () => {
          console.log(`✅ WebSocket connected for customer ${customerId}`);
          sessionStorage.setItem("customerId", customerId.toString());
          setIsLoading(false);
          navigate("/dashboard");
        };

        socket.onerror = (err) => {
          console.error("WebSocket error:", err);
          alert("WebSocket connection failed.");
          setIsLoading(false);
        };

        socket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log("📩 Message from server:", data);
        };
      } catch (err) {
        console.error("WebSocket setup error:", err);
        setIsLoading(false);
      }
    } else {
      alert("Incorrect OTP");
    }
  };

  const handleAdminLogin = () => {
    if (adminUsername === "admin" && adminPassword === "admin123") {
      sessionStorage.setItem("customerId", "0");
      navigate("/dashboard");
    } else {
      alert("Invalid admin credentials");
    }
  };

  return (
    <Box
      minH="100vh"
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
      style={{
        background: "radial-gradient(circle at top left, #f3e8ff, #ffffff)",
        backgroundImage: `url(${bgImage})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        position: "relative",
        padding: "24px",
        overflow: "hidden",
      }}
    >
      <Text
        style={{
          fontSize: "36px",
          fontWeight: "bold",
          // color: "#1a1a1a",
          color: "white",
          marginBottom: "24px",
        }}
      >
        NexTel Agent Assist
      </Text>

      <VStack
        style={{
          backgroundColor: "white",
          padding: "32px",
          borderRadius: "16px",
          boxShadow: "0 6px 20px rgba(0, 0, 0, 0.1)",
          width: "100%",
          maxWidth: "400px",
          zIndex: 1,
          alignItems: "stretch",
        }}
      >
        {!loginMode && (
          <VStack>
            <Button
              onClick={() => setLoginMode("admin")}
              colorPalette="teal"
              width="100%"
            >
              Login as Admin
            </Button>
            <Button
              onClick={() => setLoginMode("customer")}
              bgGradient="linear-gradient(to right, #a351f5, #b273ef)"
              width="100%"
            >
              Login as Customer
            </Button>
          </VStack>
        )}

        {loginMode && (
          <Button variant="ghost" onClick={() => setLoginMode(null)} mt={2}>
            🔙 Back to login options
          </Button>
        )}

        {loginMode === "admin" && (
          <>
            <Input
              placeholder="Username"
              value={adminUsername}
              onChange={(e) => setAdminUsername(e.target.value)}
            />
            <Input
              placeholder="Password"
              type="password"
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
            />
            <Button
              onClick={handleAdminLogin}
              bgGradient="linear-gradient(to right, #a351f5, #b273ef)"
              color="white"
              fontWeight="bold"
              padding="20px 0"
              width="100%"
              mt={4}
            >
              Login
            </Button>
          </>
        )}

        {loginMode === "customer" && (
          <>
            <HStack style={{ width: "100%" }}>
              <Box
                style={{
                  padding: "8px 12px",
                  backgroundColor: "#edf2f7",
                  borderTopLeftRadius: "6px",
                  borderBottomLeftRadius: "6px",
                  color: "#2d3748",
                  fontWeight: 500,
                  border: "1px solid #e2e8f0",
                }}
              >
                +91
              </Box>
              <Input
                placeholder="Phone number"
                value={phone}
                onChange={handlePhoneChange}
                maxLength={10}
                type="tel"
                style={{
                  borderTopLeftRadius: "0",
                  borderBottomLeftRadius: "0",
                }}
              />
            </HStack>

            {error && (
              <Text
                style={{
                  color: "#e53e3e",
                  fontSize: "14px",
                  marginTop: "4px",
                }}
              >
                {error}
              </Text>
            )}

            {!showOTP && (
              <Button
                onClick={handleSendOTP}
                bgGradient="linear-gradient(to right, #a351f5, #b273ef)"
                style={{
                  color: "white",
                  fontWeight: "bold",
                  padding: "20px 0",
                  width: "100%",
                  marginTop: "12px",
                }}
              >
                Send OTP
              </Button>
            )}

            {showOTP && (
              <>
                <HStack style={{ justifyContent: "center", marginTop: "8px" }}>
                  {otp.map((digit, idx) => (
                    <Input
                      key={idx}
                      ref={(el) => {
                        inputRefs.current[idx] = el;
                      }}
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOTPChange(idx, e.target.value)}
                      textAlign="center"
                      type="password"
                      style={{
                        width: "48px",
                        height: "48px",
                        fontSize: "20px",
                        fontWeight: "bold",
                      }}
                    />
                  ))}
                </HStack>

                <Skeleton
                  loading={isLoading}
                  style={{
                    marginTop: "16px",
                    width: "100%",
                  }}
                >
                  <Button
                    onClick={handleLogin}
                    bgGradient="linear-gradient(to right, #a351f5, #b273ef)"
                    color="white"
                    fontWeight="bold"
                    padding="20px 0"
                    width="100%"
                  >
                    Login
                  </Button>
                </Skeleton>
              </>
            )}
          </>
        )}
      </VStack>
    </Box>
  );
};

export default Login;
