import React from "react";
import { ChakraProvider, CSSReset } from "@chakra-ui/react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import MCPClient from "./pages/MCPClient";
import Settings from "./pages/Settings";
import Layout from "./components/Layout";

function App() {
  return (
    <ChakraProvider>
      <CSSReset />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/client" element={<MCPClient />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </Router>
    </ChakraProvider>
  );
}

export default App;
