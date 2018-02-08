import matplotlib.pyplot as plt
import seaborn as sns; sns.set()  # for plot styling
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE

def getAttributes(track):
    t_pitch = track[3]
    t_timbre = track[4]
    t_loud = track[5]
    return np.hstack((t_pitch, t_timbre, t_loud))

from dataset_processing import *

data = read_stored_data('library.data')

new = np.zeros((1, 25))
ids = []

for i in range(len(data)):
    # ID
    ids += [data[i][0]]
    # corresponding attributes
    t_attr = getAttributes(data[i])
    new = np.vstack((new, np.hstack(t_attr)))

# attributes
attr = new[1:]

enabledTsne = False

if enabledTsne is True:
    # T-SNE
    attr_tsne = TSNE(n_components=2).fit_transform(attr)

    # K-means
    kmeans = KMeans(n_clusters=13)
    kmeans.fit(attr_tsne)
    y_kmeans = kmeans.predict(attr_tsne)

    # store as .txt in a format "ID, cluster"
    data = np.column_stack((ids, y_kmeans))
    np.savetxt('genre_clusters_tsne.txt', data, delimiter=" ", fmt='%s')

    plt.scatter(attr_tsne[:, 0], attr_tsne[:, 1], c=y_kmeans, s=5, cmap='viridis')
    plt.show()

else:
    # K-means
    kmeans = KMeans(n_clusters=13)
    kmeans.fit(attr)
    y_kmeans = kmeans.predict(attr)

    # store as .txt in a format "ID, cluster"
    data = np.column_stack((ids, y_kmeans))
    np.savetxt('genre_clusters.txt', data, delimiter=" ", fmt='%s')
