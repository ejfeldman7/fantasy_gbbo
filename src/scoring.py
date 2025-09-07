from typing import Dict, List

def run_final_scoring(data: Dict, final_winner: str, final_finalists: List[str]) -> Dict[str, int]:
    """Calculates foresight points for all users based on final season results."""
    foresight_scores = {user_id: 0 for user_id in data.get('users', {})}
    
    for user_id, weekly_picks in data.get('picks', {}).items():
        for week_str, picks in weekly_picks.items():
            try:
                week_num = int(week_str)
                if picks.get('season_winner') == final_winner:
                    foresight_scores[user_id] += (11 - week_num) * 10
                if picks.get('finalist_1') in final_finalists:
                    foresight_scores[user_id] += (11 - week_num) * 5
                if picks.get('finalist_2') in final_finalists:
                    foresight_scores[user_id] += (11 - week_num) * 5
            except (ValueError, TypeError):
                continue
    return foresight_scores

def calculate_user_scores(data: Dict) -> Dict:
    """Calculates total scores, including weekly and final foresight points."""
    scores = {}
    final_scores = data.get('final_scores', {})

    for user_id, user_picks in data.get('picks', {}).items():
        weekly_points = 0
        for week, picks in user_picks.items():
            results = data.get('results', {}).get(week)
            if results:
                if picks.get('star_baker') == results.get('star_baker'):
                    weekly_points += 5
                if picks.get('eliminated_baker') == results.get('eliminated_baker'):
                    weekly_points += 5
                if picks.get('technical_winner') == results.get('technical_winner'):
                    weekly_points += 3
                if picks.get('handshake_prediction') and results.get('handshake_given'):
                    weekly_points += 10
                if picks.get('star_baker') == results.get('eliminated_baker'):
                    weekly_points -= 5
                if picks.get('eliminated_baker') == results.get('star_baker'):
                    weekly_points -= 5
                if picks.get('handshake_prediction') and not results.get('handshake_given'):
                    weekly_points -= 10
        
        foresight_points = final_scores.get(user_id, 0)
        
        scores[user_id] = {
            'weekly_points': weekly_points, 
            'foresight_points': foresight_points, 
            'total_points': weekly_points + foresight_points
        }
    return scores

