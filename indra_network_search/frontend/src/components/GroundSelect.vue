<template>

</template>

<script>
import BaseSelectBS from "@/components/BaseSelectBS";

export default {
  props: {
    /* An array of match objects
     * Example of sending {'text': 'MEK'} to grounding at
     * http://grounding.indra.bio/ground:
     * [{'match':
     *     {'cap_combos': [],
     *      'dash_mismatches': [],
     *      'exact': True,
     *      'query': 'MEK',
     *      'ref': 'MEK',
     *      'space_mismatch': False},
     *      'score': 1.0,
     *      'term': {'db': 'FPLX',
     *      'entry_name': 'MEK',
     *      'id': 'MEK',
     *      'norm_text': 'mek',
     *      'source': 'famplex',
     *      'status': 'assertion',
     *      'text': 'MEK'},
     *   'url': 'https://identifiers.org/fplx:MEK'},
     *  {'match':
     *     {'cap_combos': [],
     *      'dash_mismatches': [],
     *      'exact': True,
     *      'query': 'MEK',
     *      'ref': 'MEK',
     *      'space_mismatch': False},
     *      'score': 0.5555555555555556,
     *      'term': {'db': 'CHEBI',
     *      'entry_name': 'butan-2-one',
     *      'id': 'CHEBI:28398',
     *      'norm_text': 'mek',
     *      'source': 'chebi',
     *      'status': 'synonym',
     *      'text': 'MEK'},
     *   'url': 'https://identifiers.org/CHEBI:28398'}]
     * */
    groundingList: {
      type: Array,
      default: []
    },
  },
}
</script>
