<template>
<!-- Organize table with one row per statement type -->
  <table class="table table-sm">
    <thead>
      <tr>
        <th scope="col">Type</th>
        <th scope="col">Evidence</th>
        <th scope="col">Sources</th>
        <th scope="col">Link to DB</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(stmtDataArr, type, index) in stmtDataObj" :key="index">
        <SupportRow
          :subj-node="subjNode"
          :obj-node="objNode"
          :stmt-arr="stmtDataArr"
          :stmt-type="type"
        />
      </tr>
    </tbody>
  </table>
</template>

<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import SupportRow from "@/components/Result/SupportRow";

export default {
  components: {SupportRow},
  props: {
    objNode: {
      type: Object,
      required: true,
      validator: obj => {
        return sharedHelpers.isNode(obj)
      }
    },
    subjNode: {
      type: Object,
      required: true,
      validator: obj => {
        return sharedHelpers.isNode(obj)
      }
    },
    stmtDataObj: {
      type: Object,
      required: true,
      validator: obj => {
        // FixMe: Check that obj is { stmt_type: [stmtData, ...] }
        return !(sharedHelpers.isEmptyObject(obj));
      }
    }
  }
}
</script>
