<template>
<!--
TodO for future:
 - Add expandable area with nav components like:
   https://getbootstrap.com/docs/5.0/components/card/#navigation
   The main tab summarizing the individual statements (at this level they
   are of the same type and are only distinguished by hash)
 - The other tabs are per statement hash and loads a INDRA DB like view of
   the statement
  -->
<!-- Parent table has:
  <tr>
    <th scope="col">Type</th>
    <th scope="col">Evidence: 5</th>
    <th scope="col">Sources</th>
    <th scope="col">Link to DB</th>
  </tr>
 -->
  <td>
    <StatementTitle
      :subj-node="subjNode"
      :obj-node="objNode"
      :sentence="english"
    />
  </td>
  <td>{{ evidenceCount }}</td>
  <!-- ToDo: v-for over all sources and create badges -->
  <td><span class="badge rounded-pill bg-secondary">sparser</span></td>
  <td><a :href="linkToDB"><i class="bi bi-box-arrow-up-right"></i></a></td>
</template>
<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import StatementTitle from "@/components/Result/StatementTitle";

export default {
  components: {StatementTitle},
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
    stmtType: {
      type: String,
      required: true
    },
    stmtArr: {
      type: Array,
      required: true,
      validator: arr => {
        const notEmpty = arr.length > 0;
        const containsStmts = sharedHelpers.isStmtDataArray(arr);
        return notEmpty && containsStmts;
      }
    }
  },
  computed: {
    stmtCount() {
      // FixMe: sum up all statements (or statement types?)
      return 5
    },
    evidenceCount() {
      // FixMe: sum up all evidences
      return 10
    },
    linkToDB() {
      return `https://db.indra.bio/statements/from_agents?subject=${this.subjNode.name}&object=${this.objNode.name}&stmt_type=${this.stmtType}&format=html`;
    },
    english() {
      if (!this.stmtArr) {
        return '';
      }
      let sd = this.stmtArr[0];
      return sd.english
    }
  },
}
</script>
