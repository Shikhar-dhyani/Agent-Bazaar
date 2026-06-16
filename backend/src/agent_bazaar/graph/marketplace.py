from langgraph.graph import StateGraph, END
from agent_bazaar.graph.state import MarketplaceState
from agent_bazaar.graph.nodes import (
    decompose_node,
    select_next_subtask_node,
    collect_bids_node,
    clear_auction_node,
    execute_node,
    score_node,
    update_reputation_node,
    aggregate_node,
    route_after_select,
)


def build_marketplace_graph():
    graph = StateGraph(MarketplaceState)

    graph.add_node("decompose", decompose_node)
    graph.add_node("select_next", select_next_subtask_node)
    graph.add_node("collect_bids", collect_bids_node)
    graph.add_node("clear_auction", clear_auction_node)
    graph.add_node("execute", execute_node)
    graph.add_node("score", score_node)
    graph.add_node("update_reputation", update_reputation_node)
    graph.add_node("aggregate", aggregate_node)

    graph.set_entry_point("decompose")
    graph.add_edge("decompose", "select_next")
    graph.add_conditional_edges(
        "select_next",
        route_after_select,
        {"collect_bids": "collect_bids", "aggregate": "aggregate"},
    )
    graph.add_edge("collect_bids", "clear_auction")
    graph.add_edge("clear_auction", "execute")
    graph.add_edge("execute", "score")
    graph.add_edge("score", "update_reputation")
    graph.add_edge("update_reputation", "select_next")
    graph.add_edge("aggregate", END)

    return graph.compile()


marketplace_graph = build_marketplace_graph()
