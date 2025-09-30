"""
Smart Server Selection Service for Onix
Provides intelligent server selection based on multiple criteria
"""

import time
import threading
import statistics
import math
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
from constants import LogLevel


@dataclass
class ServerMetrics:
    """Server performance metrics."""
    ping: float = 0.0
    download_speed: float = 0.0
    upload_speed: float = 0.0
    packet_loss: float = 0.0
    jitter: float = 0.0
    uptime: float = 100.0
    last_tested: float = 0.0
    test_count: int = 0
    success_rate: float = 100.0
    load_factor: float = 0.0
    geographic_distance: float = 0.0
    timezone_offset: int = 0


@dataclass
class SelectionCriteria:
    """Server selection criteria weights."""
    ping_weight: float = 0.3
    speed_weight: float = 0.25
    stability_weight: float = 0.2
    uptime_weight: float = 0.15
    geographic_weight: float = 0.1


class SmartServerSelector:
    """Intelligent server selection system."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (
            lambda msg, level: print(f"[{level}] {msg}"))
        self._server_metrics: Dict[str, ServerMetrics] = {}
        self._selection_history: deque = deque(maxlen=100)
        self._criteria = SelectionCriteria()
        self._learning_data = defaultdict(list)
        self._user_preferences = {}
        self._is_learning = True
        self._learning_thread = None
        self._stop_learning = threading.Event()

    def update_server_metrics(self, server_id: str, metrics: Dict[str, Any]) -> None:
        """Update metrics for a specific server."""
        try:
            if server_id not in self._server_metrics:
                self._server_metrics[server_id] = ServerMetrics()

            server_metrics = self._server_metrics[server_id]

            # Update basic metrics
            if 'ping' in metrics:
                server_metrics.ping = float(metrics['ping'])
            if 'download_speed' in metrics:
                server_metrics.download_speed = float(
                    metrics['download_speed'])
            if 'upload_speed' in metrics:
                server_metrics.upload_speed = float(metrics['upload_speed'])
            if 'packet_loss' in metrics:
                server_metrics.packet_loss = float(metrics['packet_loss'])
            if 'jitter' in metrics:
                server_metrics.jitter = float(metrics['jitter'])
            if 'uptime' in metrics:
                server_metrics.uptime = float(metrics['uptime'])
            if 'load_factor' in metrics:
                server_metrics.load_factor = float(metrics['load_factor'])
            if 'geographic_distance' in metrics:
                server_metrics.geographic_distance = float(
                    metrics['geographic_distance'])
            if 'timezone_offset' in metrics:
                server_metrics.timezone_offset = int(
                    metrics['timezone_offset'])

            # Update test statistics
            server_metrics.last_tested = time.time()
            server_metrics.test_count += 1

            # Calculate success rate
            if server_metrics.test_count > 0:
                successful_tests = server_metrics.test_count * \
                    (server_metrics.success_rate / 100)
                if metrics.get('success', True):
                    successful_tests += 1
                server_metrics.success_rate = (
                    successful_tests / server_metrics.test_count) * 100

            self.log(
                f"Updated metrics for server {server_id}: ping={server_metrics.ping}ms, speed={server_metrics.download_speed}Mbps", LogLevel.DEBUG)

        except Exception as e:
            self.log(f"Error updating server metrics: {e}", LogLevel.ERROR)

    def select_best_server(self, servers: List[Dict[str, Any]],
                           user_preferences: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Select the best server based on intelligent criteria."""
        try:
            if not servers:
                return None

            # Update user preferences
            if user_preferences:
                self._user_preferences.update(user_preferences)

            # Calculate scores for each server
            scored_servers = []

            for server in servers:
                server_id = server.get('id', server.get('name', ''))
                if not server_id:
                    continue

                # Get metrics for this server
                metrics = self._server_metrics.get(server_id, ServerMetrics())

                # Calculate composite score
                score = self._calculate_server_score(server, metrics)

                scored_servers.append({
                    'server': server,
                    'score': score,
                    'metrics': metrics
                })

            # Sort by score (higher is better)
            scored_servers.sort(key=lambda x: x['score'], reverse=True)

            if not scored_servers:
                return None

            # Select the best server
            best_server_data = scored_servers[0]
            best_server = best_server_data['server']

            # Record selection for learning
            self._record_selection(best_server, best_server_data['score'])

            self.log(
                f"Selected server: {best_server.get('name', 'Unknown')} (score: {best_server_data['score']:.2f})", LogLevel.INFO)

            return best_server

        except Exception as e:
            self.log(f"Error selecting best server: {e}", LogLevel.ERROR)
            return servers[0] if servers else None

    def _calculate_server_score(self, server: Dict[str, Any], metrics: ServerMetrics) -> float:
        """Calculate a composite score for a server."""
        try:
            score = 0.0

            # Ping score (lower is better)
            if metrics.ping > 0:
                ping_score = max(0, 100 - (metrics.ping / 10)
                                 )  # 100ms = 0 score
                score += ping_score * self._criteria.ping_weight

            # Speed score (higher is better)
            if metrics.download_speed > 0:
                # 1Gbps = 100 score
                speed_score = min(100, metrics.download_speed / 10)
                score += speed_score * self._criteria.speed_weight

            # Stability score (based on packet loss and jitter)
            stability_score = 100
            if metrics.packet_loss > 0:
                stability_score -= metrics.packet_loss * 10  # 1% packet loss = -10 points
            if metrics.jitter > 0:
                # High jitter penalty
                stability_score -= min(50, metrics.jitter)
            stability_score = max(0, stability_score)
            score += stability_score * self._criteria.stability_weight

            # Uptime score
            uptime_score = metrics.uptime
            score += uptime_score * self._criteria.uptime_weight

            # Geographic score (closer is better)
            if metrics.geographic_distance > 0:
                # 1000km = 0 score
                geo_score = max(0, 100 - (metrics.geographic_distance / 1000))
                score += geo_score * self._criteria.geographic_weight

            # Apply user preferences
            score = self._apply_user_preferences(server, score)

            # Apply learning adjustments
            score = self._apply_learning_adjustments(server, score)

            return max(0, min(100, score))  # Clamp between 0 and 100

        except Exception as e:
            self.log(f"Error calculating server score: {e}", LogLevel.ERROR)
            return 50.0  # Default neutral score

    def _apply_user_preferences(self, server: Dict[str, Any], score: float) -> float:
        """Apply user preferences to the score."""
        try:
            # Time-based preferences
            current_hour = time.localtime().tm_hour
            if 'preferred_hours' in self._user_preferences:
                preferred_hours = self._user_preferences['preferred_hours']
                if current_hour in preferred_hours:
                    score *= 1.1  # 10% bonus

            # Geographic preferences
            if 'preferred_countries' in self._user_preferences:
                preferred_countries = self._user_preferences['preferred_countries']
                server_country = server.get('country', '').lower()
                if server_country in [c.lower() for c in preferred_countries]:
                    score *= 1.05  # 5% bonus

            # Protocol preferences
            if 'preferred_protocols' in self._user_preferences:
                preferred_protocols = self._user_preferences['preferred_protocols']
                server_protocol = server.get('protocol', '').lower()
                if server_protocol in [p.lower() for p in preferred_protocols]:
                    score *= 1.03  # 3% bonus

            return score

        except Exception as e:
            self.log(f"Error applying user preferences: {e}", LogLevel.WARNING)
            return score

    def _apply_learning_adjustments(self, server: Dict[str, Any], score: float) -> float:
        """Apply machine learning adjustments to the score."""
        try:
            if not self._is_learning:
                return score

            server_id = server.get('id', server.get('name', ''))
            if not server_id:
                return score

            # Get historical performance data
            historical_data = self._learning_data.get(server_id, [])
            if len(historical_data) < 5:  # Need at least 5 data points
                return score

            # Calculate performance trend
            recent_scores = [data['score']
                             for data in historical_data[-10:]]  # Last 10 selections
            if len(recent_scores) >= 3:
                trend = self._calculate_trend(recent_scores)
                score += trend * 5  # Apply trend adjustment

            # Calculate reliability factor
            reliability = self._calculate_reliability(historical_data)
            score *= reliability

            return score

        except Exception as e:
            self.log(
                f"Error applying learning adjustments: {e}", LogLevel.WARNING)
            return score

    def _calculate_trend(self, scores: List[float]) -> float:
        """Calculate performance trend from historical scores."""
        try:
            if len(scores) < 2:
                return 0.0

            # Simple linear trend calculation
            n = len(scores)
            x = list(range(n))
            y = scores

            # Calculate slope
            x_mean = sum(x) / n
            y_mean = sum(y) / n

            numerator = sum((x[i] - x_mean) * (y[i] - y_mean)
                            for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                return 0.0

            slope = numerator / denominator
            return slope  # Positive = improving, Negative = declining

        except Exception:
            return 0.0

    def _calculate_reliability(self, historical_data: List[Dict[str, Any]]) -> float:
        """Calculate reliability factor from historical data."""
        try:
            if not historical_data:
                return 1.0

            # Calculate success rate
            successful_selections = sum(
                1 for data in historical_data if data.get('success', True))
            success_rate = successful_selections / len(historical_data)

            # Calculate consistency (low variance in scores)
            scores = [data['score'] for data in historical_data]
            if len(scores) < 2:
                return success_rate

            mean_score = statistics.mean(scores)
            variance = statistics.variance(scores)
            # Lower variance = higher consistency
            consistency = max(0.5, 1.0 - (variance / 100))

            # Combine success rate and consistency
            reliability = (success_rate * 0.7) + (consistency * 0.3)

            return max(0.5, min(1.2, reliability))  # Clamp between 0.5 and 1.2

        except Exception:
            return 1.0

    def _record_selection(self, server: Dict[str, Any], score: float) -> None:
        """Record server selection for learning."""
        try:
            server_id = server.get('id', server.get('name', ''))
            if not server_id:
                return

            selection_data = {
                'server_id': server_id,
                'score': score,
                'timestamp': time.time(),
                'success': True  # Will be updated later based on actual performance
            }

            self._selection_history.append(selection_data)
            self._learning_data[server_id].append(selection_data)

            # Keep only recent data
            if len(self._learning_data[server_id]) > 50:
                self._learning_data[server_id] = self._learning_data[server_id][-50:]

        except Exception as e:
            self.log(f"Error recording selection: {e}", LogLevel.WARNING)

    def update_selection_result(self, server_id: str, success: bool, performance_metrics: Optional[Dict[str, Any]] = None) -> None:
        """Update the result of a server selection for learning."""
        try:
            # Update the most recent selection
            if self._selection_history:
                last_selection = self._selection_history[-1]
                if last_selection['server_id'] == server_id:
                    last_selection['success'] = success
                    if performance_metrics:
                        last_selection['performance'] = performance_metrics

            # Update learning data
            if server_id in self._learning_data:
                for data in self._learning_data[server_id]:
                    if data['timestamp'] == last_selection['timestamp']:
                        data['success'] = success
                        if performance_metrics:
                            data['performance'] = performance_metrics
                        break

        except Exception as e:
            self.log(f"Error updating selection result: {e}", LogLevel.WARNING)

    def set_criteria_weights(self, criteria: SelectionCriteria) -> None:
        """Set new selection criteria weights."""
        self._criteria = criteria
        self.log(f"Updated selection criteria: {criteria}", LogLevel.INFO)

    def get_server_rankings(self, servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get ranked list of servers with their scores."""
        try:
            ranked_servers = []

            for server in servers:
                server_id = server.get('id', server.get('name', ''))
                if not server_id:
                    continue

                metrics = self._server_metrics.get(server_id, ServerMetrics())
                score = self._calculate_server_score(server, metrics)

                ranked_servers.append({
                    'server': server,
                    'score': score,
                    'metrics': {
                        'ping': metrics.ping,
                        'download_speed': metrics.download_speed,
                        'upload_speed': metrics.upload_speed,
                        'packet_loss': metrics.packet_loss,
                        'uptime': metrics.uptime,
                        'success_rate': metrics.success_rate
                    }
                })

            # Sort by score
            ranked_servers.sort(key=lambda x: x['score'], reverse=True)

            return ranked_servers

        except Exception as e:
            self.log(f"Error getting server rankings: {e}", LogLevel.ERROR)
            return []

    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get performance analytics and insights."""
        try:
            analytics = {
                'total_servers': len(self._server_metrics),
                'total_selections': len(self._selection_history),
                'learning_enabled': self._is_learning,
                'criteria_weights': {
                    'ping': self._criteria.ping_weight,
                    'speed': self._criteria.speed_weight,
                    'stability': self._criteria.stability_weight,
                    'uptime': self._criteria.uptime_weight,
                    'geographic': self._criteria.geographic_weight
                },
                'top_performers': [],
                'insights': []
            }

            # Get top performing servers
            if self._server_metrics:
                server_scores = []
                for server_id, metrics in self._server_metrics.items():
                    # Create a dummy server for scoring
                    dummy_server = {'id': server_id, 'name': server_id}
                    score = self._calculate_server_score(dummy_server, metrics)
                    server_scores.append((server_id, score, metrics))

                # Sort by score and get top 5
                server_scores.sort(key=lambda x: x[1], reverse=True)
                analytics['top_performers'] = [
                    {
                        'server_id': server_id,
                        'score': score,
                        'ping': metrics.ping,
                        'download_speed': metrics.download_speed,
                        'uptime': metrics.uptime
                    }
                    for server_id, score, metrics in server_scores[:5]
                ]

            # Generate insights
            if self._selection_history:
                recent_selections = list(
                    self._selection_history)[-20:]  # Last 20 selections
                success_rate = sum(1 for s in recent_selections if s.get(
                    'success', True)) / len(recent_selections)

                analytics['insights'].append(
                    f"Recent success rate: {success_rate:.1%}")

                if success_rate < 0.8:
                    analytics['insights'].append(
                        "Consider adjusting selection criteria")

                if success_rate > 0.95:
                    analytics['insights'].append(
                        "Selection algorithm is performing excellently")

            return analytics

        except Exception as e:
            self.log(
                f"Error getting performance analytics: {e}", LogLevel.ERROR)
            return {'error': str(e)}

    def start_learning(self) -> None:
        """Start the learning process."""
        if self._is_learning:
            return

        self._is_learning = True
        self._stop_learning.clear()

        self._learning_thread = threading.Thread(
            target=self._learning_loop, daemon=True)
        self._learning_thread.start()

        self.log("Started server selection learning", LogLevel.INFO)

    def stop_learning(self) -> None:
        """Stop the learning process."""
        self._is_learning = False
        self._stop_learning.set()

        if self._learning_thread and self._learning_thread.is_alive():
            self._learning_thread.join(timeout=2)

        self.log("Stopped server selection learning", LogLevel.INFO)

    def _learning_loop(self) -> None:
        """Main learning loop."""
        while not self._stop_learning.is_set():
            try:
                # Analyze selection patterns
                self._analyze_selection_patterns()

                # Update criteria based on performance
                self._update_criteria_from_performance()

                # Clean up old data
                self._cleanup_old_data()

                time.sleep(300)  # Run every 5 minutes

            except Exception as e:
                self.log(f"Error in learning loop: {e}", LogLevel.ERROR)
                time.sleep(60)

    def _analyze_selection_patterns(self) -> None:
        """Analyze selection patterns for insights."""
        try:
            if len(self._selection_history) < 10:
                return

            # Analyze success patterns
            recent_selections = list(self._selection_history)[-50:]
            successful_selections = [
                s for s in recent_selections if s.get('success', True)]

            if len(successful_selections) < 5:
                return

            # Find patterns in successful selections
            successful_scores = [s['score'] for s in successful_selections]
            avg_successful_score = statistics.mean(successful_scores)

            # Adjust criteria if needed
            if avg_successful_score < 70:
                self.log(
                    "Low success scores detected, adjusting criteria", LogLevel.WARNING)
                # Could implement automatic criteria adjustment here

        except Exception as e:
            self.log(
                f"Error analyzing selection patterns: {e}", LogLevel.WARNING)

    def _update_criteria_from_performance(self) -> None:
        """Update criteria based on performance data."""
        try:
            # This could implement adaptive criteria adjustment
            # For now, just log that we're monitoring
            pass

        except Exception as e:
            self.log(
                f"Error updating criteria from performance: {e}", LogLevel.WARNING)

    def _cleanup_old_data(self) -> None:
        """Clean up old learning data."""
        try:
            current_time = time.time()
            cutoff_time = current_time - (30 * 24 * 3600)  # 30 days ago

            # Clean up selection history
            self._selection_history = deque(
                [s for s in self._selection_history if s['timestamp'] > cutoff_time],
                maxlen=100
            )

            # Clean up learning data
            for server_id in list(self._learning_data.keys()):
                self._learning_data[server_id] = [
                    data for data in self._learning_data[server_id]
                    if data['timestamp'] > cutoff_time
                ]

                if not self._learning_data[server_id]:
                    del self._learning_data[server_id]

        except Exception as e:
            self.log(f"Error cleaning up old data: {e}", LogLevel.WARNING)
