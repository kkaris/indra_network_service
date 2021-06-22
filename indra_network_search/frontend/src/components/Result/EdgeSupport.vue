<template>
<!-- Organize table with one row per statement type -->
  <table class="table table-sm table-borderless table-hover">
    <thead>
      <tr>
        <th scope="col">Type</th>
        <th scope="col">Sources</th>
        <th scope="col">Link to DB</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(stmtTypeSupport, type, index) in stmtDataObj" :key="index">
        <SupportRow
          :subj-node="subjNode"
          :obj-node="objNode"
          :stmt-type-support="stmtTypeSupport"
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
      // Follows EdgeData.statements: Dict[str, StmtTypeSupport]
      type: Object,
      required: true,
      validator: obj => {
        // The values, [stmtData, ...], is checked by child component SupportRow
        return !(sharedHelpers.isEmptyObject(obj));
      }
    }
  }
}
</script>
