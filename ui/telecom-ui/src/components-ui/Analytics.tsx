/* eslint-disable @typescript-eslint/no-unused-vars */
import { useEffect, useState } from "react";
import {
  SimpleGrid,
  Box,
  Text,
  Badge,
  HStack,
  Skeleton,
  Spinner,
} from "@chakra-ui/react";
const apiBaseUrl = import.meta.env.VITE_BASE_URL;

type AnalyticsData = {
  id: number;
  session_id: string;
  user_id: string;
  datetime: string;
  title: string;
  intent: string[];
  sentiment_score: number;
  topics: string[];
  issue_resolved: boolean;
  satisfaction: string;
};

const Analytics = () => {
  const [data, setData] = useState<AnalyticsData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://${apiBaseUrl}/conversation_analytics`)
      .then((res) => res.json())
      .then((result) => {
        if (result.success) {
          setData(result.data);
          setLoading(false);
        } else {
          setLoading(false);
          console.error("API error: success=false");
        }
      })
      .catch((error) => {
        setLoading(false);
        console.error("Failed to fetch analytics data:", error);
      })
      .finally(() => setLoading(false));
  }, []);

  const getSentimentColor = (score: number) => {
    if (score > 0.3) return "#48BB78"; // green-400
    if (score < -0.3) return "#F56565"; // red-400
    return "#ED8936"; // orange-400
  };

  return (
    <Box
      px={6}
      py={8}
      style={{
        minHeight: "100vh",
        // background:
        //   "radial-gradient(circle at top left, #d6bcfa 0%, #e9d8fd 60%, #f3ebff 100%)",
        // color: "#382c40",
      }}
    >
      <Text fontSize="3xl" fontWeight="bold" mb={8}>
        Conversation Analytics
      </Text>
      <Skeleton loading={loading} height="100%">
        <SimpleGrid
          columns={{ base: 1, md: 2 }}
          style={{
            gap: "24px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          }}
        >
          {data.map((item) => (
            <Box
              key={item.id}
              style={{
                // background: "rgba(255, 255, 255, 0.15)", // Glass effect
                backdropFilter: "blur(12px)",
                // WebkitBackdropFilter: "blur(8px)",
                borderRadius: "24px",
                boxShadow:
                  "0 8px 20px 0 rgba(0, 0, 0, 0.2), 0 0 1px 0 rgba(255, 255, 255, 0.12)", // Gray shadow
                padding: "24px",
                border: "1px solid rgba(255, 255, 255, 0.18)",
                color: "#4a4a4a",
                marginBottom: "24px",
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
              }}
            >
              <Text
                style={{
                  fontWeight: "700",
                  fontSize: "1.2rem",
                  marginBottom: "8px",
                }}
              >
                {item.title}
              </Text>

              <Text
                style={{
                  fontSize: "0.85rem",
                  color: "#4a4a4a",
                  fontWeight: "500",
                  textShadow: "0 0 4px rgba(0,0,0,0.1)",
                  marginBottom: "12px",
                }}
              >
                {item.datetime} — Session ID: {item.session_id}
              </Text>

              <HStack
                style={{
                  gap: "12px",
                  marginBottom: "16px",
                }}
              >
                <Badge
                  style={{
                    backgroundColor: item.issue_resolved
                      ? "#48BB78"
                      : "#F56565",
                    color: "white",
                    padding: "6px 14px",
                    borderRadius: "12px",
                    fontWeight: "600",
                    fontSize: "0.8rem",
                    boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
                    userSelect: "none",
                  }}
                >
                  {item.issue_resolved ? "Resolved" : "Unresolved"}
                </Badge>

                <Badge
                  style={{
                    backgroundColor: getSentimentColor(item.sentiment_score),
                    color: "white",
                    padding: "6px 14px",
                    borderRadius: "12px",
                    fontWeight: "600",
                    fontSize: "0.8rem",
                    boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
                    userSelect: "none",
                  }}
                >
                  Sentiment: {item.sentiment_score.toFixed(2)}
                </Badge>

                <Badge
                  style={{
                    backgroundColor: "#718096", // gray-600
                    color: "white",
                    padding: "6px 14px",
                    borderRadius: "12px",
                    fontWeight: "600",
                    fontSize: "0.8rem",
                    boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
                    userSelect: "none",
                  }}
                >
                  {item.satisfaction}
                </Badge>
              </HStack>

              <Text
                style={{
                  fontSize: "0.9rem",
                  userSelect: "none",
                  textShadow: "0 0 2px rgba(0,0,0,0.1)",
                  marginBottom: "6px",
                }}
              >
                <strong>Intents:</strong> {item.intent.join(", ")}
              </Text>
              <Text
                style={{
                  fontSize: "0.9rem",
                  userSelect: "none",
                  textShadow: "0 0 2px rgba(0,0,0,0.1)",
                }}
              >
                <strong>Topics:</strong> {item.topics.join(", ")}
              </Text>
            </Box>
          ))}
        </SimpleGrid>
      </Skeleton>
    </Box>
  );
};

export default Analytics;
