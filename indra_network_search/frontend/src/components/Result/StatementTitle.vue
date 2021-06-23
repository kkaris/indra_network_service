<template>
  <span>
    <Node v-bind="subjNode"/> {{ linkedSentence }} <Node v-bind="objNode" />
  </span>
</template>

<script>
import Node from "@/components/Result/Node";
import sharedHelpers from "@/helpers/sharedHelpers";

export default {
  components: {Node},
  props: {
    subjNode: {
      type: Object,
      required: true,
      validator: obj => {
        return sharedHelpers.isNode(obj)
      }
    },
    objNode: {
      type: Object,
      required: true,
      validator: obj => {
        return sharedHelpers.isNode(obj)
      }
    },
    sentence: {
      // Simple english string from statements
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
