<template>
<!--
TodO for future:
 - Add expandable area with nav components like:
   https://getbootstrap.com/docs/5.0/components/card/#navigation
   The main tab could summarize the individual statements (at this level
   they are of the same type and are only distinguished by hash)
 - The other tabs are per statement hash and loads a INDRA DB like view of
   the statement
  -->
<!-- Parent table has:
  <tr>
    <th scope="col">Type</th>
    <th scope="col">Sources</th>
    <th scope="col">Link to DB</th>
  </tr>
 -->
  <td>{{ stmtType }}</td>
  <td style="text-align: end">
    <SourceDisplay :source_counts="stmtTypeSupport.source_counts" />
  </td>
  <td><a :href="linkToDB"><i class="bi bi-box-arrow-up-right"></i></a></td>
</template>
<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import SourceDisplay from "@/components/Result/SourceDisplay";

export default {
  components: {SourceDisplay},
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
    stmtTypeSupport: {
      // Follows StmtTypeSupport
      type: Object,
      required: true,
      validator: obj => {
        const notEmpty = !sharedHelpers.isEmptyObject(obj);
        const isStmtTypeSupport = sharedHelpers.isStmtTypeSupport(obj);
        return notEmpty && isStmtTypeSupport;
      }
    }
  },
  computed: {
    stmtCount() {
      return this.stmtTypeSupport.statements.length;
    },
    linkToDB() {
      return `https://db.indra.bio/statements/from_agents?subject=${this.subjNode.name}&object=${this.objNode.name}&type=${this.stmtType}&format=html`;
    },
    english() {
      if (!this.stmtTypeSupport.statements ||
          !this.stmtTypeSupport.statements.length) {
        return 'No statements in data!';
      }
      let sd = this.stmtTypeSupport.statements[0];
      return sd.english
    },
    sourceCount() {
      return sharedHelpers.getSourceCounts(this.stmtTypeSupport);
    }
  },
}
</script>
