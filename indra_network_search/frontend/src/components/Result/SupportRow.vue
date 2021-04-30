<template>
<!-- Parent table has:
  <tr>
    <th scope="col">Type</th>
    <th scope="col">Evidence: 5</th>
    <th scope="col">Sources</th>
    <th scope="col">Link to DB</th>
  </tr>
 -->
  <td>{{ stmtType }}</td>
  <td>{{ evidenceCount }}</td>
  <!-- ToDo: v-for over all sources and create badges -->
  <td><span class="badge badge-pill badge-secondary">sparser</span></td>
  <td><a :href="linkToDB"><i class="bi bi-box-arrow-up-right"></i></a></td>
</template>
<script>
import sharedHelpers from "@/helpers/sharedHelpers";

export default {
  props: {
    objName: {
      type: String,
      required: true
    },
    subjName: {
      type: String,
      required: true
    },
    stmtType: {
      type: String,
      required: true
    },
    stmtArr: {
      type: Array,
      required: true,
      validator: arr => {
        // TodO: validate that array is not empty and contains stmtData
        const notEmpty = arr.length > 0;
        const containsStmts = arr.every(sharedHelpers.isStmtData);
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
      return `https://db.indra.bio/statements/from_agents?subject=
      ${this.subjName}&object=${this.objName}&stmt_type=${this.stmtType}
      &format=html`;
    }
  },
}
</script>
