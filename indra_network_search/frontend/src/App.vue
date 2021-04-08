<template>
  <NetworkSearchForm/>
  <!-- Put Results Here -->
</template>

<script>
import NetworkSearchForm from "@/components/NetworkSearchForm";

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
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
