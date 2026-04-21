import axios from "axios";

const http = axios.create({
  baseURL: "/api/v1",
  timeout: 15000,
});

http.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
);

export default http;
