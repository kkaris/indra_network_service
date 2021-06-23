import axios from "axios";

const apiClient = axios.create({
  baseURL: "https://network.indra.bio/dev",
  withCredentials: false,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});

export default {
  submitForm(networkSearchQuery) {
    return apiClient.post("/query", networkSearchQuery);
  },
};
