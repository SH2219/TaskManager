import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ToastContainer } from "react-toastify";
import App from "./App";
import "./index.css";
import "react-toastify/dist/ReactToastify.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
    <ToastContainer theme="colored" newestOnTop closeButton limit={4} />
  </StrictMode>,
);
