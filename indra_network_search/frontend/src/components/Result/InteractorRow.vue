<template>
  <!-- Edge with source -->
  <div class="row">
    <div class="col-2">Source edge:</div>
    <div class="col"><Edge v-bind="sourceEdgeData" /></div>
  </div>
  <!-- Edge with source -->
  <div class="row">
    <div class="col-2">Target edge:</div>
    <div class="col"><Edge v-bind="targetEdgeData" /></div>
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
