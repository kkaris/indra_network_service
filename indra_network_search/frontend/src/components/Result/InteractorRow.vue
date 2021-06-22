<template>
  <!-- Edge with source -->
  <div class="row">
    <Edge v-bind="sourceEdgeData" />
  </div>
  <!-- Edge with source -->
  <div class="row">
    <Edge v-bind="targetEdgeData" />
  </div>
</template>

<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import Edge from "@/components/Result/Edge";

export default {
  components: { Edge },
  props: {
    sourceEdgeData: {
      type: Object,
      required: true,
      validator: obj => {
        return sharedHelpers.isEdgeData(obj)
      }
    },
    targetEdgeData: {
      type: Object,
      required: true,
      validator: obj => {
        return sharedHelpers.isEdgeData(obj)
      }
    }
  }
}
</script>
