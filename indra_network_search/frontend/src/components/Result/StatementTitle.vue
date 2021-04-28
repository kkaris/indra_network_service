<template>
  <span>
    <Node v-bind="subj_node"/> {{ linkedSentence }} <Node v-bind="obj_node" />
  </span>
</template>

<script>
import Node from "@/components/Result/Node";

export default {
  components: {Node},
  props: {
    subj_node: {
      type: Object,
      required: true,
      validator: obj => {
        return obj.name && obj.identifier && obj.namespace
      }
    },
    obj_node: {
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
          .replace(this.subj_node.name, '')
          .replace(this.obj_node.name, '')
    }
  }
};
</script>
