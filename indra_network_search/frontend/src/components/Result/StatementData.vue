<template>
  <div class="container border rounded-lg">
    <h3>
      <StatementTitle
        :subj_node="subj_node"
        :obj_node="obj_node"
        :sentence="english"
      /></h3>
      <p class="d-inline-flex p-2 bd-highlight border rounded-sm">
        <span>Evidence: {{ evidence_count }}| </span>
        <span> Curated: {{ curated }}| </span>
        <span> <a :href="db_url_hash">View in INDRA DB</a></span>
      </p>
  </div>
</template>

<script>
import StatementTitle from "@/components/Result/StatementTitle";

export default {
  components: {StatementTitle},
  props: {
    // Pass nodes to StatmentTitle
    subj_node: {
      type: Object,
      required: true,
    },
    obj_node: {
      type: Object,
      required: true,
    },
    // Match the fields of Class StmtData in indra_network_search/data_models.py
    stmt_type: {
      type: String,
      required: true,
    },
    evidence_count: {
      type: Number,
      required: true,
    },
    stmt_hash: {
      type: String,
      required: true,
    },
    source_counts: {
      type: Object,
      required: true,
    },
    belief: {
      type: Number,
      required: true,
    },
    curated: {
      type: Boolean,
      required: true,
    },
    english: {
      type: String,
      required: true,
    },
    weight: {
      type: [String, Number],
      default: '',
    },
    residue: {
      type: String,
      default: '',
    },
    position: {
      type: String,
      default: '',
    },
    initial_sign: {
      type: Number,
      default: null,
    },
    db_url_hash: {
      type: String,
      required: true,
    },
  },
};
</script>
