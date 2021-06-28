<template>
  <div class="container">
    <div class="row d-flex justify-content-center">
      <div class="col-5">
        <Node v-bind="subjNode" /><i class="bi bi-arrow-right"></i><Node v-bind="objNode" />
      </div>
      <div class="col-5 text-end">
        <SourceDisplay :source_counts="source_counts" />
      </div>
      <div class="col">
        <span><a :href="db_url_edge"><i class="bi bi-box-arrow-up-right"></i></a></span>
      </div>
      <div class="col">
        <a
          role="button"
          class="text-reset"
          data-bs-toggle="collapse"
          :href="`#${strUUID}`"
          :aria-expanded="false"
          :aria-controls="strUUID"
        >
          <i title="Click to expand" class="bi-plus-circle"></i>
        </a>
      </div>
    </div>
    <div class="row collapse" :id="strUUID">
      <EdgeSupport
          :subj-node="subjNode"
          :obj-node="objNode"
          :stmt-data-obj="statements"
      />
    </div>
  </div>
</template>

<script>
import Node from "@/components/Result/Node";
import EdgeSupport from "@/components/Result/EdgeSupport";
import sharedHelpers from "@/helpers/sharedHelpers";
import UniqueID from "@/helpers/BasicHelpers";
import SourceDisplay from "@/components/Result/SourceDisplay";
export default {
  components: {SourceDisplay, EdgeSupport, Node},
  props: {
    // Follows BaseModel indra_network_search.data_models::EdgeData
    edge: {
      // List[Node] - Edge supported by statements
      type: Array,
      required: true,
      validator: arr => {
        const arrLen = arr.length > 0;
        const containsNodes = arr.every(sharedHelpers.isNode);

        return arrLen && containsNodes
      }
    },
    statements: {
      // Dict[str, StmtTypeSupport] - key by stmt_type
      type: Object,
      required: true,
      validator: obj => {
        return Object.keys(obj).length > 0;
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
    },
    source_counts: {
      type: Object,
      required: true,
      validator: obj => {
        return sharedHelpers.isSourceCount(obj)
      }
    }
  },
  setup() {
    const uuid = UniqueID().getID();
    return {
      uuid
    }
  },
  computed: {
    subjNode() {
      return this.edge[0]
    },
    objNode() {
      return this.edge[1]
    },
    strUUID() {
      return `collapse-${this.uuid}`
    }
  }
}
</script>
