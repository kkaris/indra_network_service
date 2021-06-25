<template>
  <NetworkSearchForm/>
</template>

<script>
import NetworkSearchForm from "@/views/NetworkSearchForm";

export default {
  name: "App",
  components: {
    NetworkSearchForm,
  },
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
