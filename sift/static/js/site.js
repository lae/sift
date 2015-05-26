var PlayerRank = React.createClass({
    render: function() {
        return (
            <tr>
                <td className="tracker-number">{this.props.rank}</td>
                <td className="tracker-player-name">{this.props.name}</td>
                <td className="tracker-number">{this.props.score}</td>
            </tr>
        );
    }
});

var PlayerRankLegend = React.createClass({
    render: function() {
        return (
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Name</th>
                    <th>Score</th>
                </tr>
            </thead>
        );
    }
});

var RankSplitList = React.createClass({
    render: function() {
        return (
            <div className="pure-u-1 pure-u-md-1 pure-u-xl-1-4 tracker-container">
                <div className="tracker-box">
                    <table className="tracker-table">
                        <PlayerRankLegend />
                        <tbody>
                            {this.props.content}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    }
});

var RankList = React.createClass({
    render: function() {
        var playerNodes = this.props.players.map(function (player) {
            return (
                <PlayerRank rank={player.rank} name={player.name} score={player.score} />
            );
        });
        var splitPlayerNodes = [
            playerNodes.slice(0, 25),
            playerNodes.slice(25, 50),
            playerNodes.slice(50, 75),
            playerNodes.slice(75, 100)
        ];
        var splitList = splitPlayerNodes.map(function (sp) {
            return (
                <RankSplitList content={sp} />
            );
        });
        return (
            <div className="tracker-wrapper pure-g">
                {splitList}
            </div>
        );
    }
});

React.render(
    <RankList players={players} />,
    document.body
);
