<template>
  <NetworkSearchForm/>
  <ResultArea/>
</template>

<script>
import NetworkSearchForm from "@/views/NetworkSearchForm";
import ResultArea from "@/views/ResultArea"

export default {
  name: "App",
  components: {
    ResultArea,
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
