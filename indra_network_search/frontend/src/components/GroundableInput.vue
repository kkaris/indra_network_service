<template>
  <BaseInputBS
    v-model="modelValue"
    label="{{ label }}"
    type="text"
  />
  <button
    class="button btn btn-primary btn-mini"
    type="button"
    :onclick="getGrounding"
    :disabled="awaitingGrounding"
  >Ground with Gilda</button>
  <span>
    <!-- ToDo: create new select component that takes the Gilda return
          values as input -->
  </span>
</template>

<script>
import BaseInputBS from "@/components/BaseInputBS";
import AxiosMethods from "@/services/AxiosMethods";
import BaseSelectBS from "@/components/BaseSelectBS";

export default {
  components: {BaseSelectBS, BaseInputBS},
  props: {
    label: {
      type: String,
      default: ''
    },
    modelValue: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      groundData: [],
      awaitingGrounding: false,
    }
  },
  methods: {
    getGrounding(agentText) {
      this.awaitingGrounding = true;
      AxiosMethods.submitGrounding(agentText)
      .then(response => {
        this.groundData = response.data;
        this.awaitingGrounding = false
      })
      .catch(error => {
        console.log(error);
        this.awaitingGrounding = false
      })
    }
  }
}
</script>
