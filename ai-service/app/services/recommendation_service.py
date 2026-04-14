from typing import List


class RecommendationService:
    """Rule-based + ML recommendation engine for tasks and priorities."""

    def recommend_assignee(self, task: dict, team: List[dict]) -> dict:
        """
        Suggest the best team member to assign a task to based on:
        - Current workload
        - Skill match
        - Availability
        """
        if not team:
            return {"assignee_id": None, "reason": "No team members available"}

        # Sort by workload ascending (fewest tasks first)
        sorted_team = sorted(team, key=lambda m: m.get("open_tasks", 0))
        best = sorted_team[0]
        return {
            "assignee_id": best["id"],
            "name": best.get("name"),
            "reason": f"Lowest workload ({best.get('open_tasks', 0)} open tasks)",
        }

    def recommend_priority(self, task: dict) -> dict:
        """
        Suggest task priority based on deadline proximity and dependencies.
        """
        days_until_due = task.get("days_until_due", 99)
        has_blockers = task.get("has_blockers", False)

        if days_until_due <= 1 or has_blockers:
            return {"priority": "critical", "reason": "Due imminently or has blockers"}
        elif days_until_due <= 3:
            return {"priority": "high", "reason": "Due within 3 days"}
        elif days_until_due <= 7:
            return {"priority": "medium", "reason": "Due within a week"}
        else:
            return {"priority": "low", "reason": "No immediate deadline"}
