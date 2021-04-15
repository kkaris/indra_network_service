import "bootstrap/dist/css/bootstrap.min.css";
import "@dafcoe/vue-collapsible-panel/dist/vue-collapsible-panel.css";
import { createApp } from "vue";
import App from "./App.vue";
import VueCollapsiblePanel from "@dafcoe/vue-collapsible-panel";

const app = createApp(App);
app.use(VueCollapsiblePanel).mount("#app");
