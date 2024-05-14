def merge_clusters_until_convergence(
        clusters: list
) -> list:

    while True:
        idx_sets_to_be_merged = _get_idx_sets_to_be_merged(clusters)
        if not idx_sets_to_be_merged:
            break
        
        clusters = _merge_clusters(clusters, idx_sets_to_be_merged)

    return clusters


def _get_idx_sets_to_be_merged(
        clusters: list[list],
) -> list[set]:

    to_be_merged = []
    for i, cls1 in enumerate(clusters):
        for j, cls2 in enumerate(clusters):
            if i < j:
                if set(cls1) & set(cls2):
                    flag_add = False
                    for idx_set in to_be_merged:
                        if i in idx_set:
                            idx_set.add(j)
                            flag_add = True
                            break

                        elif j in idx_set:
                            idx_set.add(i)
                            flag_add = True
                            break

                    if not flag_add:
                        to_be_merged.append(set([i, j]))

    return to_be_merged


def _merge_clusters(
        clusters: list[list],
        idx_set_to_be_merged: list[set],
) -> list[list]:

    new_clusters = []
    idx_used = set()
    for idx_set in idx_set_to_be_merged:
        new_set = list(set(sum([clusters[idx] for idx in idx_set], [])))
        idx_used |= idx_set
        new_clusters.append(new_set)

    for idx, cls in enumerate(clusters):
        if not idx in idx_used:
            new_clusters.append(cls)

    return new_clusters
