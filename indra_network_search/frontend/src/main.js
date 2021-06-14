import "@popperjs/core/dist/cjs/popper";
import "bootstrap/dist/js/bootstrap.min";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import "./assets/sources.css";
import { createApp } from "vue";
import App from "./App.vue";

const app = createApp(App);
app.mount("#app");
