<template>
  <Node v-bind="subjNode" />
  <i class="bi bi-arrow-right"></i>
  <Node v-bind="objNode" />
  <a class="badge badge-primary">{{ stmtCount }}</a>
  <span class="badge badge-pill badge-secondary">{{ evidenceCount }}</span>
  <span><a :href="db_url_edge"><i class="bi bi-box-arrow-up-right"></i></a></span>
  <EdgeSupport
    :subj-node="subjNode"
    :obj-node="objNode"
    :stmt-data-obj="statements"
  />
</template>

<script>
import Node from "@/components/Result/Node";
import EdgeSupport from "@/components/Result/EdgeSupport";
import sharedHelpers from "@/helpers/sharedHelpers";
export default {
  components: {EdgeSupport, Node},
  props: {
    // Follows BaseModel indra_network_search.data_models::EdgeData
    edge: {
      type: Array,
      required: true,
      validator: arr => {
        const arrLen = arr.length > 0;
        const containsNodes = arr.every(sharedHelpers.isNode);

        return arrLen && containsNodes
      }
    },
    statements: {
      type: Object,
      required: true,
      validator: obj => {
        const hasEl = Object.keys(obj).length > 0;
        // const containsStmtData = sharedHelpers.isObjectOf(obj, )
        const containsStmtData = true;

        return hasEl && containsStmtData
      }
    },
    belief: {
      type: Number,
      required: true
    },
    weight: {
      type: Number,
      required: true
    },
    sign: {
      type: Number,
      default: null
    },
    context_weight: {
      type: [Number, String],
      default: 'N/A'
    },
    db_url_edge: {
      type: String,
      required: true
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
    subjNode() {
      return this.edge[0]
    },
    objNode() {
      return this.edge[1]
    }
  }
}
</script>
