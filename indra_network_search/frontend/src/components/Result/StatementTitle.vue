<template>
  <span>
    <Node v-bind="subjNode"/> {{ linkedSentence }} <Node v-bind="objNode" />
  </span>
</template>

<script>
import Node from "@/components/Result/Node";

export default {
  components: {Node},
  props: {
    subjNode: {
      type: Object,
      required: true,
      validator: obj => {
        return obj.name && obj.identifier && obj.namespace
      }
    },
    objNode: {
      type: Object,
      required: true,
      validator: obj => {
        return obj.name && obj.identifier && obj.namespace
      }
    },
    sentence: {
      type: String,
      required: true,
    }
  },
  computed: {
    linkedSentence() {
      return this.sentence
          .replace(this.subjNode.name, '')
          .replace(this.objNode.name, '')
    }
  }
};
</script>
