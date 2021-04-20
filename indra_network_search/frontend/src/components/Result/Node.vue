<template>
  <span>
    <a v-if="lookup" :href="lookup" :title="title"><b>{{ name }}</b></a>
    <b v-else :title="title">{{ name }}</b>
  </span>
</template>

<script>
export default {
  // Match the fields of class Node in indra_network_search/data_models.py
  props: {
    name: {
      type: String,
      default: ''
    },
    namespace: {
      type: String,
      required: true
    },
    identifier: {
      type: String,
      required: true
    },
    sign: {
      // Currently unused in this context
      type: Number,
      default: null
    },
    lookup: {
      type: String,
      default: ''
    },
  },
  computed: {
    title() {
      return `${this.namespace}:${this.identifier}`
    }
  }
}
</script>
