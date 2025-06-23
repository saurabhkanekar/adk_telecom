/* eslint-disable @typescript-eslint/no-explicit-any */
import { Box, Button, Flex, Text, VStack } from "@chakra-ui/react";
import { useState } from "react";
import Chatbot from "@/components-ui/Chatbot";
import Analytics from "@/components-ui/Analytics";
import { useNavigate } from "react-router-dom";

const Dashboard = () => {
  const navigate = useNavigate();

  // const [value, setValue] = useState<string>("chatbot");
  const [value, setValue] = useState<string>(
    sessionStorage.getItem("customerId") === "0" ? "analytics" : "chatbot"
  );

  const handleLogout = () => {
    sessionStorage.clear();
    (window as any).chatWebSocket?.close();
    navigate("/");
  };

  const HEADER_HEIGHT = "64px";
  const SIDEBAR_WIDTH = "200px";

  return (
    <Box minH="100vh" bg="gray.50">
      {/* Top Navbar */}
      <Flex
        position="fixed"
        top="0"
        left="0"
        right="0"
        height={HEADER_HEIGHT}
        bg="white"
        px={6}
        align="center"
        justify="space-between"
        borderBottom="1px solid"
        borderColor="gray.200"
        zIndex="1000"
      >
        <Text
          fontSize="xl"
          fontWeight="bold"
          //   bgGradient="linear-gradient(to right, #fc8181, #f687b3)" // soft red-pink
          color="#382c40"
          //   bgClip={"text"}
        >
          NexTel Agent Assist
        </Text>
        <Button
          colorPalette="red"
          variant="outline"
          onClick={handleLogout}
          className="!rounded-sm"
        >
          Logout
        </Button>
      </Flex>

      {/* Main Layout */}
      <Flex>
        {/* Sidebar */}
        <VStack
          position="fixed"
          top={HEADER_HEIGHT}
          left="0"
          width={SIDEBAR_WIDTH}
          height={`calc(100vh - ${HEADER_HEIGHT})`}
          bg="white"
          p={4}
          borderRight="1px solid"
          borderColor="gray.200"
          align="stretch"
        >
          {/* <Button
            variant="ghost"
            className={`!rounded-lg ${
              value === "chatbot"
                ? "!bg-[#bbdaff] !text-gray-900"
                : "!bg-transparent"
            }`}
            onClick={() => setValue("chatbot")}
          >
            Chatbot
          </Button>
          <Button
            variant="ghost"
            className={`!rounded-lg 
                ${
                  value === "analytics"
                    ? "!bg-[#bbdaff] !text-gray-900"
                    : "!bg-transparent"
                }
            `}
            onClick={() => setValue("analytics")}
          >
            Analytics
          </Button> */}
          {value === "chatbot" && (
            <Button
              variant={value === "chatbot" ? "subtle" : "ghost"}
              colorPalette="purple"
              className="!rounded-lg"
              onClick={() => setValue("chatbot")}
            >
              Chatbot
            </Button>
          )}

          {value === "analytics" && (
            <Button
              variant={value === "analytics" ? "subtle" : "ghost"}
              colorPalette="purple"
              className="!rounded-lg"
              onClick={() => setValue("analytics")}
            >
              Analytics
            </Button>
          )}
        </VStack>

        {/* Content Area */}
        <Box
          p={6}
          flex="1"
          ml={SIDEBAR_WIDTH}
          pt={HEADER_HEIGHT}
          height={`calc(100vh - ${HEADER_HEIGHT})`}
          overflowY="auto"
        >
          {value === "chatbot" && <Chatbot />}
          {value === "analytics" && <Analytics />}
        </Box>
      </Flex>
    </Box>
  );
};

export default Dashboard;
